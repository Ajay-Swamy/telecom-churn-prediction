"""Input rules for one customer. Field names match the Kaggle CSV columns exactly."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Reusable "allowed values" types.
YesNo = Literal["Yes", "No"]
YesNoNoInternet = Literal["Yes", "No", "No internet service"]

# The six add-on columns that depend on having internet service.
INTERNET_ADDONS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]


class Customer(BaseModel):
    gender: Literal["Female", "Male"]
    SeniorCitizen: Literal[0, 1]
    Partner: YesNo
    Dependents: YesNo
    tenure: int = Field(ge=0, le=120, description="Months as a customer")
    PhoneService: YesNo
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: YesNoNoInternet
    OnlineBackup: YesNoNoInternet
    DeviceProtection: YesNoNoInternet
    TechSupport: YesNoNoInternet
    StreamingTV: YesNoNoInternet
    StreamingMovies: YesNoNoInternet
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: YesNo
    PaymentMethod: Literal[
        "Electronic check", "Mailed check",
        "Bank transfer (automatic)", "Credit card (automatic)",
    ]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)

    # Shows a ready-made example in the /docs page.
    model_config = {
        "json_schema_extra": {
            "example": {
                "gender": "Female", "SeniorCitizen": 0, "Partner": "No",
                "Dependents": "No", "tenure": 12, "PhoneService": "Yes",
                "MultipleLines": "No", "InternetService": "Fiber optic",
                "OnlineSecurity": "No", "OnlineBackup": "No",
                "DeviceProtection": "No", "TechSupport": "No",
                "StreamingTV": "Yes", "StreamingMovies": "Yes",
                "Contract": "Month-to-month", "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 89.5, "TotalCharges": 1074.0,
            }
        }
    }

    # Runs after the single-field checks pass. Catches rows that contradict themselves.
    @model_validator(mode="after")
    def check_consistency(self):
        if self.PhoneService == "No" and self.MultipleLines != "No phone service":
            raise ValueError("MultipleLines must be 'No phone service' when PhoneService is 'No'")
        if self.PhoneService == "Yes" and self.MultipleLines == "No phone service":
            raise ValueError("MultipleLines cannot be 'No phone service' when PhoneService is 'Yes'")

        for name in INTERNET_ADDONS:
            value = getattr(self, name)
            if self.InternetService == "No" and value != "No internet service":
                raise ValueError(f"{name} must be 'No internet service' when InternetService is 'No'")
            if self.InternetService != "No" and value == "No internet service":
                raise ValueError(f"{name} cannot be 'No internet service' when the customer has internet")
        return self




class PredictionResponse(BaseModel):
    churn_probability: float                 
    prediction: Literal["Churn", "No Churn"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    recommendations: list[str]
    threshold: float                         
    model_version: str



class BatchRequest(BaseModel):
    # Between 1 and 1000 customers per request, to protect the server from huge uploads.
    customers: list[Customer] = Field(min_length=1, max_length=1000)


class BatchResponse(BaseModel):
    count: int
    predictions: list[PredictionResponse]   # same order as the input


    