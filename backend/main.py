import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI

from backend.risk import get_recommendations, get_risk_level
from backend.schemas import (BatchRequest, BatchResponse, Customer,
                             PredictionResponse)

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "model"

# Load once at startup. If these files are missing, the server fails immediately
# with a clear error, which is better than failing later on the first request.
pipeline = joblib.load(MODEL_DIR / "churn_pipeline.joblib")
metadata = json.loads((MODEL_DIR / "model_metadata.json").read_text())
THRESHOLD = metadata["threshold"]
MODEL_VERSION = metadata["model_version"]

app = FastAPI(title="Telecom Churn Prediction API")


def make_response(customer: Customer, probability: float) -> PredictionResponse:
    """Turn one customer + its churn probability into the API response."""
    risk_level = get_risk_level(probability, THRESHOLD)
    return PredictionResponse(
        churn_probability=round(probability, 4),
        prediction="Churn" if probability >= THRESHOLD else "No Churn",
        risk_level=risk_level,
        recommendations=get_recommendations(customer, risk_level),
        threshold=THRESHOLD,
        model_version=MODEL_VERSION,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model_version": MODEL_VERSION}


@app.post("/predict", response_model=PredictionResponse)
def predict(customer: Customer):
    # The pipeline expects a table, so wrap the one customer in a 1-row DataFrame.
    row = pd.DataFrame([customer.model_dump()])
    # predict_proba returns [[P(stays), P(churns)]], so [0, 1] picks P(churns).
    probability = float(pipeline.predict_proba(row)[0, 1])
    return make_response(customer, probability)


@app.post("/predict/batch", response_model=BatchResponse)
def predict_batch(request: BatchRequest):
    # One table for ALL customers, one pipeline call: much faster than a loop.
    rows = pd.DataFrame([c.model_dump() for c in request.customers])
    probabilities = pipeline.predict_proba(rows)[:, 1]

    # zip pairs each customer with its own probability, keeping the original order.
    predictions = [
        make_response(customer, float(p))
        for customer, p in zip(request.customers, probabilities)
    ]
    return BatchResponse(count=len(predictions), predictions=predictions)