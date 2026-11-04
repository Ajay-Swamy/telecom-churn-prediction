"""Dashboard page: screenshots of the Power BI report, plus a link to the file."""
from pathlib import Path

import streamlit as st

# assets/ sits next to app.py, one level above this pages/ folder.
ASSETS = Path(__file__).resolve().parent.parent / "assets"
PBIX_URL = ("https://github.com/Ajay-Swamy/telecom-churn-prediction"
            "/blob/main/dashboard/telecom_churn_dashboard.pbix")

st.set_page_config(page_title="Power BI dashboard", page_icon="📈", layout="wide")
st.title("📈 Power BI dashboard")
st.write(
    "A business-intelligence view of the same Telco customer data, built in Power BI. "
    "It summarises churn by customer status, contract, internet service, payment method "
    "and demographics."
)
st.info(
    "These are **static screenshots**, so the filters on them don't work here. "
    "The interactive report is the `.pbix` file in the GitHub repository. "
    "Open it with Power BI Desktop (Windows)."
)
st.link_button("Get the interactive Power BI file (GitHub)", PBIX_URL)


def show(file_name: str, caption: str) -> None:
    """Show one screenshot, or a warning if the file is missing."""
    path = ASSETS / file_name
    if path.exists():
        st.image(str(path), width="stretch")
    else:
        st.warning(f"Image not found: {file_name}")
    st.caption(caption)


tab_overview, tab_demographics = st.tabs(["Overview", "Demographics"])

with tab_overview:
    show("dashboard1.png",
         "Overview: key figures, customer status, and churn by contract type, "
         "internet service and payment method.")

with tab_demographics:
    show("dashboard2.png",
         "Demographics: churn by gender, partner, senior citizen and dependents.")