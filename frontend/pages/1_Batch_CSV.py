"""Batch page: upload a CSV of customers, score them all, download the results."""
import hashlib
import io
import json
import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
CHUNK_SIZE = 1000   # the API accepts at most 1000 customers per request

# The 19 columns the model needs (same names as the Kaggle CSV).
REQUIRED_COLUMNS = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges",
]

# One example row, so people can download a correctly shaped file.
SAMPLE_ROW = {
    "customerID": "EXAMPLE-001", "gender": "Female", "SeniorCitizen": 0, "Partner": "No",
    "Dependents": "No", "tenure": 12, "PhoneService": "Yes", "MultipleLines": "No",
    "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
    "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
    "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check", "MonthlyCharges": 89.5, "TotalCharges": 1074.0,
}

st.set_page_config(page_title="Batch scoring", page_icon="📄", layout="wide")
st.title("📄 Batch scoring")
st.write(
    "Upload a CSV with one customer per row. Every customer gets a churn probability and "
    "a risk level, sorted so the riskiest customers are first."
)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Check the columns exist and fix TotalCharges the same way train.py did."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error("Your file is missing these columns: " + ", ".join(missing))
        st.stop()
    df = df.copy()
    # Blank TotalCharges becomes NaN; for brand-new customers (tenure 0) that means 0.
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df.loc[df["TotalCharges"].isna() & (df["tenure"] == 0), "TotalCharges"] = 0
    return df


def score(df: pd.DataFrame) -> list[dict]:
    """Send the customers to the API in chunks and collect the predictions."""
    # to_json -> json.loads guarantees plain Python numbers/strings (safe to send).
    records = json.loads(df[REQUIRED_COLUMNS].to_json(orient="records"))
    predictions = []
    progress = st.progress(0.0, text="Scoring customers...")

    for start in range(0, len(records), CHUNK_SIZE):
        chunk = records[start:start + CHUNK_SIZE]
        try:
            response = requests.post(f"{API_URL}/predict/batch",
                                     json={"customers": chunk}, timeout=60)
        except requests.RequestException:
            st.error("Cannot reach the API. Is it running?")
            st.stop()

        if response.status_code == 422:
            st.error("The API rejected some rows. Fix them in your file and upload it again:")
            for problem in response.json()["detail"][:10]:   # show at most 10
                loc = problem["loc"]   # e.g. ["body", "customers", 4, "Contract"]
                if len(loc) > 2 and isinstance(loc[2], int):
                    row = start + loc[2] + 2   # +2: line 1 is the header, files count from 1
                    column = loc[3] if len(loc) > 3 else "(a combination of columns)"
                    st.markdown(f"- **Row {row}**, column **{column}**: {problem['msg']}")
                else:
                    st.markdown(f"- {problem['msg']}")
            st.stop()
        if response.status_code != 200:
            st.error(f"Unexpected API error (status {response.status_code}).")
            st.stop()

        predictions.extend(response.json()["predictions"])
        progress.progress(min((start + CHUNK_SIZE) / len(records), 1.0))

    progress.empty()
    return predictions


def build_results(df: pd.DataFrame, predictions: list[dict]) -> pd.DataFrame:
    """Your original columns + the model's answers, riskiest first."""
    scored = pd.DataFrame(predictions)
    scored["recommendations"] = scored["recommendations"].apply("; ".join)
    scored["churn_%"] = (scored["churn_probability"] * 100).round(1)

    results = df.reset_index(drop=True)
    for col in ["churn_%", "churn_probability", "prediction", "risk_level", "recommendations"]:
        results[col] = scored[col]
    return results.sort_values("churn_probability", ascending=False)


# ---------- Upload ----------
uploaded = st.file_uploader("Upload a CSV file", type="csv")

if uploaded is None:
    st.info(f"Your file needs these {len(REQUIRED_COLUMNS)} columns: "
            + ", ".join(REQUIRED_COLUMNS)
            + ". Extra columns such as customerID or Churn are allowed and are kept in the results.")
    st.download_button("Download a sample CSV",
                       pd.DataFrame([SAMPLE_ROW]).to_csv(index=False).encode("utf-8"),
                       file_name="sample_customers.csv", mime="text/csv")
    st.stop()

# Streamlit re-runs this script on every click. Hashing the file lets us score it ONCE
# and reuse the result when you filter or download.
raw = uploaded.getvalue()
key = hashlib.md5(raw).hexdigest()

if st.session_state.get("batch_key") != key:
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError):
        st.error("That file could not be read as a CSV.")
        st.stop()
    if df.empty:
        st.error("The file has no rows.")
        st.stop()

    df = prepare(df)
    predictions = score(df)
    st.session_state.batch_results = build_results(df, predictions)
    st.session_state.batch_key = key

full = st.session_state.batch_results

# ---------- Summary ----------
counts = full["risk_level"].value_counts().reindex(["HIGH", "MEDIUM", "LOW"], fill_value=0)
flagged = (counts["HIGH"] + counts["MEDIUM"]) / len(full)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Customers", f"{len(full):,}")
m2.metric("High risk", f"{counts['HIGH']:,}")
m3.metric("Medium risk", f"{counts['MEDIUM']:,}")
m4.metric("Low risk", f"{counts['LOW']:,}")
m5.metric("Flagged for churn", f"{flagged:.1%}")

# ---------- Table ----------
selected = st.multiselect("Show risk levels", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM"])
shown = full[full["risk_level"].isin(selected)]
st.caption(f"Showing {len(shown):,} of {len(full):,} customers, riskiest first.")

id_cols = ["customerID"] if "customerID" in full.columns else []
st.dataframe(
    shown[id_cols + ["churn_%", "risk_level", "tenure", "Contract", "MonthlyCharges", "recommendations"]],
    hide_index=True,
    column_config={
        "churn_%": st.column_config.ProgressColumn("Churn probability", format="%.1f%%",
                                                   min_value=0, max_value=100),
    },
)

# ---------- Download (all rows, not just the filtered view) ----------
st.download_button("Download full results (CSV)", full.to_csv(index=False).encode("utf-8"),
                   file_name="churn_predictions.csv", mime="text/csv")
st.caption("Recommendations are simple business rules, not model output.")