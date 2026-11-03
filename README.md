# Telecom Customer Churn Prediction

[![Tests](https://github.com/Ajay-Swamy/telecom-churn-prediction/actions/workflows/tests.yml/badge.svg)](https://github.com/Ajay-Swamy/telecom-churn-prediction/actions/workflows/tests.yml)

A machine learning service that estimates how likely a telecom customer is to leave (churn), with a REST API, a web interface, automated tests and Docker deployment. It turns a notebook analysis into a deployed, tested application.

## Live demo

| | Link |
|---|---|
| Web app (Streamlit) | https://churn-frontend-mjej.onrender.com/ |
| API health check | https://churn-api-es2u.onrender.com/health |
| API docs (interactive) | https://churn-api-es2u.onrender.com/docs |

> **Note:** both services run on a free hosting tier that goes to sleep after about 15 minutes without traffic. The first visit after a quiet period can take up to a minute while the services wake up. The web app shows a "waking up" message while it waits.

## What it does

- **Single customer form:** enter one customer's details and get a churn probability, a risk level (LOW / MEDIUM / HIGH) and suggested retention actions.
- **Batch CSV upload:** upload a file of customers, score every row, filter by risk level and download the results. Invalid rows are reported with the exact row number and column.
- **REST API:** `POST /predict`, `POST /predict/batch` and `GET /health`, with strict input validation.

## Architecture

```
Browser --> Streamlit frontend --> FastAPI backend --> scikit-learn pipeline (churn_pipeline.joblib)
```

- The **frontend** never loads the model. It calls the API over HTTP.
- The **API** loads the saved pipeline once at startup and validates every request with Pydantic before it reaches the model.
- **Training** (`model/train.py`) is a separate script that produces the model file. Serving and training are independent.

## Model and results

**Data:** the public Telco Customer Churn dataset (7,043 customers, 19 input features, about 26.5% churn).

**Model:** logistic regression inside a single scikit-learn `Pipeline` (scaling + one-hot encoding + model), so the exact same preprocessing runs in training and in production.

**Test-set results** (1,409 held-out customers, decision threshold 0.35, evaluated once after all choices were made):

| Metric | Value |
|---|---|
| ROC-AUC | 0.842 |
| Recall (churners caught) | 0.706 |
| Precision (flagged customers who really churn) | 0.544 |
| F1 | 0.615 |

Confusion matrix: 264 churners caught, 110 missed, 221 false alarms, 814 correct "stays".

Accuracy is deliberately not the headline number: a model that always predicts "stays" would already be 73.5% accurate on this data.

## Key decisions

- **One pipeline, not scattered preprocessing.** The original notebooks encoded data in three separate places. A hand-written encoder could silently mis-handle a typo (for example `"Fiber Optic"` instead of `"Fiber optic"`). The saved pipeline raises an error on unknown categories, and the API rejects them earlier with a clear message.
- **No test-set leakage.** The scaler is fitted inside the pipeline, so cross-validation never sees validation data during scaling. All model and threshold choices used cross-validation on the training data only; the test set was used once at the end.
- **Threshold chosen deliberately.** Cross-validation showed regularisation strength barely changed AUC (0.844 to 0.846), so the default `C=1` was kept. The decision threshold was moved from 0.5 to 0.35, which raised recall from about 54% to about 72% in cross-validation at the cost of more false alarms. This is a business trade-off: missing a churner usually costs more than an unnecessary retention offer.
- **Honest probabilities.** `class_weight="balanced"` was tested and rejected: it did not improve AUC and inflates predicted probabilities.
- **Logistic regression over random forest.** The two scored almost the same, so the simpler model was chosen for speed, explainability and a tiny model file (a few KB).
- **Input validation beyond types.** Besides allowed values and ranges, the API rejects contradictory rows (for example "no phone service" with "multiple lines: Yes"), because the model never saw such customers in training.

## API

Interactive docs: `/docs` on the API URL.

**`POST /predict`**: one customer. Example request body:

```json
{
  "gender": "Female", "SeniorCitizen": 0, "Partner": "No", "Dependents": "No",
  "tenure": 12, "PhoneService": "Yes", "MultipleLines": "No",
  "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
  "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
  "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check", "MonthlyCharges": 89.5, "TotalCharges": 1074.0
}
```

Example response:

```json
{
  "churn_probability": 0.7269,
  "prediction": "Churn",
  "risk_level": "HIGH",
  "recommendations": ["Priority: personal retention call this week", "..."],
  "threshold": 0.35,
  "model_version": "1.0.0"
}
```

**`POST /predict/batch`**: `{"customers": [ ... ]}` with 1 to 1000 customers. Returns `{"count": N, "predictions": [ ... ]}` in the same order as the input. Invalid input returns HTTP 422, with the row index of the problem.

**`GET /health`**: returns the status and the model version.

Risk levels: LOW below the 0.35 threshold, MEDIUM from 0.35 to 0.60, HIGH from 0.60 up. The suggested actions are simple business rules, not model output.

## Run it locally

Requires Python 3.14 (the model file is tied to the exact scikit-learn version in `requirements.txt`).

```bash
# 1. Create and activate a virtual environment, then install dependencies
python -m venv venv
venv\Scripts\activate            # Windows PowerShell: .\venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install -r frontend/requirements.txt

# 2. (Optional) retrain the model from the raw CSV in data/raw
python model/train.py

# 3. Start the API
python -m uvicorn backend.main:app

# 4. In a second terminal, start the frontend
python -m streamlit run frontend/app.py
```

The API runs on http://127.0.0.1:8000 and the frontend on http://localhost:8501.

### With Docker

```bash
docker compose up --build
```

Then open http://localhost:8501. Inside Docker Compose the frontend reaches the API by its service name (`http://api:8000`), set through the `API_URL` environment variable.

## Tests

```bash
python -m pytest -v
```

22 automated tests cover valid and invalid input, contradictory rows, the batch endpoint (ordering, size limits, row-level errors), consistency between single and batch predictions, and the risk-level boundaries. GitHub Actions runs them on every push on a clean Linux machine.

## Deployment

Both services are deployed on Render as separate Docker web services built from this repository:

- **API:** root `Dockerfile`, environment variable `PORT=8000`, health check path `/health`.
- **Frontend:** `frontend/Dockerfile` with `frontend` as the build context, environment variables `PORT=8501` and `API_URL` set to the API's public URL.

## Project structure

```
backend/        FastAPI app (main.py, schemas.py, risk.py)
frontend/       Streamlit app (app.py, pages/1_Batch_CSV.py) + its own Dockerfile
model/          train.py, churn_pipeline.joblib, model_metadata.json
notebooks/      Original exploration: cleaning, EDA, features, models, evaluation
data/raw/       Telco-Customer-Churn.csv
tests/          pytest suite
Dockerfile      API image
docker-compose.yml
```

## Limitations

- **Snapshot data.** In this dataset, churned customers' tenure and total charges stop growing when they leave, so part of what the model learns reflects how long customers stayed, which a real company would not know in advance for a customer about to leave. Treat it as a demonstration, not a production-grade predictor.
- **Precision/recall trade-off.** At the 0.35 threshold, roughly 45% of flagged customers would have stayed anyway.
- **Public, historical data.** The model is trained on one public dataset and is not validated against any real company's customers.
- **Recommendations are rules,** not learned from data.
- **No authentication or database by design.** The service is stateless and uses public data. A real deployment handling customer data would need access control, logging and monitoring.
- **Free hosting.** Cold starts of up to a minute, and limited memory.

## Tech stack

Python, pandas, scikit-learn, FastAPI, Pydantic, Uvicorn, Streamlit, pytest, Docker, Docker Compose, GitHub Actions, Render.

## Data source

Telco Customer Churn dataset, publicly available on Kaggle.