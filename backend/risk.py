"""Risk levels and recommendations.
The recommendations are simple business RULES, not output from the model."""
from backend.schemas import Customer

HIGH_RISK_PROBABILITY = 0.60


def get_risk_level(probability: float, threshold: float) -> str:
    if probability >= HIGH_RISK_PROBABILITY:
        return "HIGH"
    if probability >= threshold:
        return "MEDIUM"
    return "LOW"


def get_recommendations(customer: Customer, risk_level: str) -> list[str]:
    if risk_level == "LOW":
        return []  # predicted to stay, no action needed

    tips = []
    has_internet = customer.InternetService != "No"

    if customer.Contract == "Month-to-month":
        tips.append("Offer a discount for moving to a 1- or 2-year contract")
    if customer.tenure < 12:
        tips.append("New customer: schedule an onboarding check-in call")
    if has_internet and customer.TechSupport == "No":
        tips.append("Offer a free trial of tech support")
    if customer.InternetService == "Fiber optic" and customer.MonthlyCharges > 70:
        tips.append("Review pricing: offer a loyalty discount or a cheaper plan")
    if customer.PaymentMethod == "Electronic check":
        tips.append("Encourage automatic payment with a small bill credit")

    if not tips:
        tips.append("Send a short satisfaction survey")
    if risk_level == "HIGH":
        tips.insert(0, "Priority: personal retention call this week")

    return tips[:5]  # keep the list short and readable