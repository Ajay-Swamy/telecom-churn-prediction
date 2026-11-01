import os

import requests
import streamlit as st

# Where the API lives. Set the API_URL environment variable to point elsewhere.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Colours for each risk level. Change these to restyle the result card.
RISK_COLORS = {"LOW": "#16a34a", "MEDIUM": "#d97706", "HIGH": "#dc2626"}
VERDICTS = {
    "LOW": "Likely to stay",
    "MEDIUM": "Likely to churn",
    "HIGH": "Very likely to churn",
}

st.set_page_config(page_title="Churn Predictor", page_icon="📞", layout="wide")

# ---------- Custom styling (CSS) ----------
# Colours use rgba/currentColor so the page looks right in light AND dark mode.
st.markdown(
    """
<style>
.block-container {padding-top: 4.5rem; max-width: 1200px;}
.hero {padding: 1.5rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;
       background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white;}
.hero-title {font-size: 1.9rem; font-weight: 700; line-height: 1.2;}
.hero-sub {opacity: 0.9; margin-top: 0.3rem;}
.result-card {border: 1px solid rgba(128,128,128,0.35); border-radius: 16px;
              padding: 1.4rem 1.6rem; margin-top: 1rem;}
.badge {display: inline-block; color: white; font-weight: 700; font-size: 0.8rem;
        letter-spacing: 0.06em; padding: 0.25rem 0.8rem; border-radius: 999px;}
.big-number {font-size: 3.6rem; font-weight: 800; line-height: 1.1; margin-top: 0.6rem;}
.verdict {font-size: 1.15rem; font-weight: 600; margin-top: 0.2rem;}
.muted {opacity: 0.7;}
.small {font-size: 0.85rem;}
.bar {position: relative; height: 12px; border-radius: 6px; margin: 1.2rem 0 0.5rem;
      background: rgba(128,128,128,0.25);}
.fill {height: 100%; border-radius: 6px;}
.marker {position: absolute; top: -6px; bottom: -6px; border-left: 2px dashed currentColor;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div class="hero-title">📞 Telecom Churn Predictor</div>'
    '<div class="hero-sub">Describe a customer and estimate how likely they are to leave.</div></div>',
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("API status")
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        health.raise_for_status()
        st.success(f"Online (model v{health.json()['model_version']})")
    except requests.RequestException:
        st.error("Cannot reach the API. Is it running?")
    st.divider()
    st.caption(
        "A logistic regression model trained on the public Telco Customer Churn "
        "dataset. Probabilities are estimates, not certainties."
    )


def yes_no(value: bool) -> str:
    """Toggle (True/False) -> the 'Yes'/'No' text the API expects."""
    return "Yes" if value else "No"


if "result" not in st.session_state:
    st.session_state.result = None   # remembers the last prediction between clicks

left, right = st.columns([3, 2], gap="large")

# ================= LEFT: the inputs =================
with left:
    tab_profile, tab_services, tab_billing = st.tabs(["👤 Profile", "📡 Services", "💳 Billing"])

    with tab_profile:
        gender = st.radio("Gender", ["Female", "Male"], horizontal=True)
        tenure = st.slider("Tenure (months with the company)", 0, 72, 12,
                           help="The training data covers 0 to 72 months.")
        p1, p2, p3 = st.columns(3)
        senior = p1.toggle("Senior citizen")
        partner = p2.toggle("Has a partner")
        dependents = p3.toggle("Has dependents")

    with tab_services:
        phone = st.toggle("Phone service", value=True)
        if phone:
            multiple_lines = yes_no(st.toggle("Multiple lines"))
        else:
            multiple_lines = "No phone service"   # forced, matches the API's rule
            st.caption("Multiple lines: not applicable (no phone service)")

        internet = st.radio("Internet service", ["Fiber optic", "DSL", "No"], horizontal=True)

        ADDONS = {
            "OnlineSecurity": "Online security",
            "OnlineBackup": "Online backup",
            "DeviceProtection": "Device protection",
            "TechSupport": "Tech support",
            "StreamingTV": "Streaming TV",
            "StreamingMovies": "Streaming movies",
        }
        addon_values = {}
        if internet == "No":
            st.caption("Internet add-ons: not applicable (no internet service)")
            for field in ADDONS:
                addon_values[field] = "No internet service"   # forced, matches the API's rule
        else:
            st.markdown("**Add-ons**")
            a1, a2 = st.columns(2)
            for i, (field, label) in enumerate(ADDONS.items()):
                column = a1 if i % 2 == 0 else a2
                addon_values[field] = yes_no(column.toggle(label))

    with tab_billing:
        contract = st.radio("Contract", ["Month-to-month", "One year", "Two year"], horizontal=True)
        payment = st.selectbox("Payment method", [
            "Electronic check", "Mailed check",
            "Bank transfer (automatic)", "Credit card (automatic)",
        ])
        paperless = st.toggle("Paperless billing", value=True)
        m1, m2 = st.columns(2)
        monthly = m1.number_input("Monthly charges ($)", min_value=0.0, value=89.5, step=1.0)
        total = m2.number_input("Total charges so far ($)", min_value=0.0, value=1074.0, step=10.0,
                                help="Roughly tenure x monthly charges. Use 0 for a brand-new customer.")

# Build the request exactly as the API expects (same field names as before).
customer = {
    "gender": gender,
    "SeniorCitizen": 1 if senior else 0,
    "Partner": yes_no(partner),
    "Dependents": yes_no(dependents),
    "tenure": int(tenure),
    "PhoneService": yes_no(phone),
    "MultipleLines": multiple_lines,
    "InternetService": internet,
    **addon_values,
    "Contract": contract,
    "PaperlessBilling": yes_no(paperless),
    "PaymentMethod": payment,
    "MonthlyCharges": float(monthly),
    "TotalCharges": float(total),
}


def result_card(result: dict) -> str:
    """The big coloured card, built as HTML. Only our own values go in, no user text."""
    p, t, level = result["churn_probability"], result["threshold"], result["risk_level"]
    color = RISK_COLORS[level]
    return (
        '<div class="result-card">'
        f'<span class="badge" style="background:{color}">{level} RISK</span>'
        f'<div class="big-number" style="color:{color}">{p:.1%}</div>'
        f'<div class="verdict">{VERDICTS[level]}</div>'
        '<div class="muted small">estimated probability of churn</div>'
        '<div class="bar">'
        f'<div class="fill" style="width:{p * 100:.1f}%; background:{color}"></div>'
        f'<div class="marker" style="left:{t * 100:.1f}%"></div>'
        "</div>"
        f'<div class="muted small">Dashed line = decision threshold ({t:.0%}). '
        "Above it, the model predicts churn.</div>"
        "</div>"
    )


# ================= RIGHT: the prediction =================
with right:
    st.subheader("Prediction")
    clicked = st.button("Predict churn risk", type="primary")

    if clicked:
        try:
            response = requests.post(f"{API_URL}/predict", json=customer, timeout=10)
        except requests.RequestException:
            st.session_state.result = None
            st.error("Cannot reach the API. Is it running?")
        else:
            if response.status_code == 200:
                st.session_state.result = response.json()
            elif response.status_code == 422:
                st.session_state.result = None
                st.error("The API rejected these values:")
                for problem in response.json()["detail"]:
                    st.markdown(f"- **{problem['loc'][-1]}**: {problem['msg']}")
            else:
                st.session_state.result = None
                st.error(f"Unexpected API error (status {response.status_code}).")

    result = st.session_state.result
    if result:
        st.markdown(result_card(result), unsafe_allow_html=True)

        if result["recommendations"]:
            with st.container(border=True):
                st.markdown("**Suggested actions**")
                for tip in result["recommendations"]:
                    st.markdown(f"- {tip}")

        st.caption(
            f"Model v{result['model_version']}. Showing the last prediction: change values "
            "and click Predict again to update. Suggested actions are simple business "
            "rules, not model output."
        )
    elif not clicked:
        st.info("Fill in the customer details on the left, then click **Predict churn risk**.")