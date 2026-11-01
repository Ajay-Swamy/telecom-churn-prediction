import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.risk import get_recommendations, get_risk_level
from backend.schemas import Customer

# Fake browser that talks directly to the app (no server needed).
client = TestClient(app)

# A valid high-risk customer (same one you used in /docs).
VALID_CUSTOMER = {
    "gender": "Female", "SeniorCitizen": 0, "Partner": "No", "Dependents": "No",
    "tenure": 12, "PhoneService": "Yes", "MultipleLines": "No",
    "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
    "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
    "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check", "MonthlyCharges": 89.5, "TotalCharges": 1074.0,
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_returns_well_formed_prediction():
    response = client.post("/predict", json=VALID_CUSTOMER)
    assert response.status_code == 200

    body = response.json()
    assert 0 <= body["churn_probability"] <= 1
    assert body["prediction"] in ("Churn", "No Churn")
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert isinstance(body["recommendations"], list)


def test_stable_customer_scores_lower_than_risky_one():
    # Same customer, but on a 2-year contract with 5 years of tenure.
    stable = {**VALID_CUSTOMER, "Contract": "Two year", "tenure": 60, "TotalCharges": 5000.0}

    risky_prob = client.post("/predict", json=VALID_CUSTOMER).json()["churn_probability"]
    stable_prob = client.post("/predict", json=stable).json()["churn_probability"]

    assert stable_prob < risky_prob





# ---------- Bad input must be rejected with 422 ----------

# @parametrize runs the SAME test once per row below, so 7 checks for the price of 1 function.
@pytest.mark.parametrize("field, bad_value", [
    ("Contract", "Month to month"),   # missing hyphens
    ("gender", "Other"),              # not an allowed value
    ("tenure", -5),                   # below the minimum
    ("tenure", 200),                  # above the maximum
    ("MonthlyCharges", -10.0),        # negative money
    ("SeniorCitizen", 2),             # must be 0 or 1
    ("PaymentMethod", "Cash"),        # not an allowed value
])
def test_invalid_value_is_rejected(field, bad_value):
    bad = {**VALID_CUSTOMER, field: bad_value}
    assert client.post("/predict", json=bad).status_code == 422


def test_missing_field_is_rejected():
    incomplete = {k: v for k, v in VALID_CUSTOMER.items() if k != "Contract"}
    assert client.post("/predict", json=incomplete).status_code == 422


def test_phone_contradiction_is_rejected():
    # No phone service, but claims multiple lines.
    bad = {**VALID_CUSTOMER, "PhoneService": "No", "MultipleLines": "Yes"}
    assert client.post("/predict", json=bad).status_code == 422


def test_internet_contradiction_is_rejected():
    # No internet service, but the add-ons still say Yes/No instead of "No internet service".
    bad = {**VALID_CUSTOMER, "InternetService": "No"}
    assert client.post("/predict", json=bad).status_code == 422


# ---------- Unusual but VALID customers must be accepted ----------
# These guard against the validator being too strict.

def test_customer_without_internet_is_accepted():
    addons = ["OnlineSecurity", "OnlineBackup", "DeviceProtection",
              "TechSupport", "StreamingTV", "StreamingMovies"]
    ok = {**VALID_CUSTOMER, "InternetService": "No", "MonthlyCharges": 20.0,
          "TotalCharges": 240.0, **{name: "No internet service" for name in addons}}
    assert client.post("/predict", json=ok).status_code == 200


def test_customer_without_phone_is_accepted():
    ok = {**VALID_CUSTOMER, "PhoneService": "No", "MultipleLines": "No phone service"}
    assert client.post("/predict", json=ok).status_code == 200


# ---------- Batch endpoint ----------

def test_batch_keeps_input_order():
    stable = {**VALID_CUSTOMER, "Contract": "Two year", "tenure": 60, "TotalCharges": 5000.0}
    response = client.post("/predict/batch", json={"customers": [VALID_CUSTOMER, stable]})
    assert response.status_code == 200

    body = response.json()
    assert body["count"] == 2
    # Risky customer was sent first, so it must come back first.
    assert body["predictions"][0]["churn_probability"] > body["predictions"][1]["churn_probability"]


def test_batch_matches_single_prediction():
    single = client.post("/predict", json=VALID_CUSTOMER).json()["churn_probability"]
    batch = client.post("/predict/batch", json={"customers": [VALID_CUSTOMER]}).json()
    assert batch["predictions"][0]["churn_probability"] == single


def test_empty_batch_is_rejected():
    assert client.post("/predict/batch", json={"customers": []}).status_code == 422


def test_oversized_batch_is_rejected():
    too_many = {"customers": [VALID_CUSTOMER] * 1001}   # limit is 1000
    assert client.post("/predict/batch", json=too_many).status_code == 422


def test_batch_error_points_to_the_bad_row():
    bad_row = {**VALID_CUSTOMER, "Contract": "Two years"}
    response = client.post("/predict/batch", json={"customers": [VALID_CUSTOMER, bad_row]})
    assert response.status_code == 422

    # Each error has a "loc" (location). Row index 1 = the second customer.
    locations = [error["loc"] for error in response.json()["detail"]]
    assert any(loc[:3] == ["body", "customers", 1] for loc in locations)


# ---------- Risk levels and recommendations (no API needed) ----------

def test_risk_levels_follow_the_threshold():
    assert get_risk_level(0.10, 0.35) == "LOW"
    assert get_risk_level(0.35, 0.35) == "MEDIUM"   # exactly at the threshold
    assert get_risk_level(0.59, 0.35) == "MEDIUM"
    assert get_risk_level(0.60, 0.35) == "HIGH"


def test_recommendations_match_risk_level():
    customer = Customer(**VALID_CUSTOMER)
    assert get_recommendations(customer, "LOW") == []
    high = get_recommendations(customer, "HIGH")
    assert high[0].startswith("Priority")
    assert len(high) <= 5