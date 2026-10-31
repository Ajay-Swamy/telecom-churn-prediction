"""Train the churn model and save it as ONE pipeline file."""
import json
import sys
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import (StratifiedKFold, cross_val_predict,
                                     cross_validate, train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Build paths from this file's location, so they work from any folder (and in Docker).
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "Telco-Customer-Churn.csv"

MODEL_DIR = ROOT / "model"
C_VALUE = 1.0        # chosen from the cross-validation table
THRESHOLD = 0.35     # chosen from the threshold table (best F1, fewer flagged customers)
MODEL_VERSION = "1.0.0"

# The 19 raw input columns, grouped by how each one must be prepared.
NUMERIC_COLS = ["tenure", "MonthlyCharges", "TotalCharges"]   # need scaling
PASSTHROUGH_COLS = ["SeniorCitizen"]                          # already 0/1, leave alone
CATEGORICAL_COLS = [                                          # text -> numbers
    "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
    "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies", "Contract",
    "PaperlessBilling", "PaymentMethod",
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV)

    # Force TotalCharges to a number; anything that isn't a number becomes NaN.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    # Blanks should only happen when tenure == 0 (brand-new customers).
    # This check makes the script fail loudly if that is ever not true.
    blank_rows = df[df["TotalCharges"].isna()]
    assert (blank_rows["tenure"] == 0).all(), "Blank TotalCharges found for non-new customers!"

    df["TotalCharges"] = df["TotalCharges"].fillna(0)
    return df


def split_data(df: pd.DataFrame):
    y = (df["Churn"] == "Yes").astype(int)          # 1 = churn, 0 = stays
    X = df.drop(columns=["customerID", "Churn"])    # 19 raw input columns
    return train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)


def build_pipeline(C: float = 1.0, class_weight=None) -> Pipeline:
    """Raw customer columns in -> churn probability out."""
    preprocess = ColumnTransformer([
        ("numbers", StandardScaler(), NUMERIC_COLS),
        ("categories", OneHotEncoder(drop="if_binary"), CATEGORICAL_COLS),
        ("senior", "passthrough", PASSTHROUGH_COLS),
    ])
    model = LogisticRegression(C=C, class_weight=class_weight, max_iter=1000)
    return Pipeline([("prep", preprocess), ("model", model)])


def compare_candidates(X_train, y_train) -> pd.DataFrame:
    """Score several settings with 5-fold cross-validation (test set NOT used)."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = ["roc_auc", "precision", "recall", "f1"]
    rows = []
    for C in [0.01, 0.1, 1, 10]:
        for weight in [None, "balanced"]:
            scores = cross_validate(build_pipeline(C, weight), X_train, y_train,
                                    cv=cv, scoring=scoring)
            rows.append({
                "C": C,
                "class_weight": str(weight),
                "AUC": scores["test_roc_auc"].mean(),
                "precision": scores["test_precision"].mean(),
                "recall": scores["test_recall"].mean(),
                "F1": scores["test_f1"].mean(),
            })
    return pd.DataFrame(rows)

def threshold_table(X_train, y_train) -> pd.DataFrame:
    """Precision/recall/F1 at different cutoffs, using out-of-fold probabilities."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    # Each customer is scored by a model that did NOT train on them.
    probs = cross_val_predict(build_pipeline(C=1.0), X_train, y_train,
                              cv=cv, method="predict_proba")[:, 1]
    rows = []
    for t in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
        pred = (probs >= t).astype(int)
        rows.append({
            "threshold": t,
            "precision": precision_score(y_train, pred),
            "recall": recall_score(y_train, pred),
            "F1": f1_score(y_train, pred),
            "flagged_%": pred.mean() * 100,   # share of customers flagged as churn
        })
    return pd.DataFrame(rows)


def train_and_save(X_train, X_test, y_train, y_test) -> None:
    # Fit on the training data only.
    pipeline = build_pipeline(C=C_VALUE).fit(X_train, y_train)

    # The one-time exam on the sealed test set.
    probs = pipeline.predict_proba(X_test)[:, 1]
    pred = (probs >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    metrics = {
        "roc_auc": round(float(roc_auc_score(y_test, probs)), 4),
        "precision": round(float(precision_score(y_test, pred)), 4),
        "recall": round(float(recall_score(y_test, pred)), 4),
        "f1": round(float(f1_score(y_test, pred)), 4),
        "true_negatives": int(tn), "false_positives": int(fp),
        "false_negatives": int(fn), "true_positives": int(tp),
    }
    print("Test-set results at threshold", THRESHOLD)
    for name, value in metrics.items():
        print(f"  {name}: {value}")

    # Save the pipeline, plus a small file describing how it was made.
    joblib.dump(pipeline, MODEL_DIR / "churn_pipeline.joblib")
    metadata = {
        "model_version": MODEL_VERSION,
        "trained_on": str(date.today()),
        "threshold": THRESHOLD,
        "C": C_VALUE,
        "python_version": sys.version.split()[0],
        "scikit_learn_version": sklearn.__version__,
        "input_columns": list(X_train.columns),
        "test_metrics": metrics,
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    print("\nSaved: model/churn_pipeline.joblib and model/model_metadata.json")


if __name__ == "__main__":
    df = load_data()
    X_train, X_test, y_train, y_test = split_data(df)
    print("X_train:", X_train.shape, "| X_test:", X_test.shape, "\n")
    train_and_save(X_train, X_test, y_train, y_test)