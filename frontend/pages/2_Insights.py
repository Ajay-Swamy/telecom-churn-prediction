"""Insights page: the main churn patterns found in the exploratory analysis."""
from pathlib import Path

import streamlit as st

# assets/ sits next to app.py, one level above this pages/ folder.
ASSETS = Path(__file__).resolve().parent.parent / "assets"

st.set_page_config(page_title="Data insights", page_icon="📊", layout="wide")
st.title("📊 What drives churn?")
st.write(
    "Charts from the exploratory analysis of the Telco Customer Churn dataset "
    "(7,043 customers). They describe the data itself, not the model's predictions."
)

# (image file, heading, takeaway). Every number below was computed from the dataset.
CHARTS = [
    ("churn_distribution.png", "How many customers leave?",
     "26.5% of customers churned (1,869 of 7,043), so the classes are imbalanced."),
    ("contract_vs_churn.png", "Contract type",
     "Month-to-month customers churn 42.7% of the time, one-year 11.3%, two-year 2.8%."),
    ("internet_vs_churn.png", "Internet service",
     "Fiber optic customers churn 41.9% of the time, versus 19.0% for DSL."),
    ("payment_vs_churn.png", "Payment method",
     "Electronic-check payers churn 45.3% of the time; the other three methods are 15% to 19%."),
    ("tenure_vs_churn.png", "Tenure",
     "Customers who churned had a median tenure of 10 months, versus 38 for those who stayed."),
]

# Two charts per row, so the rows line up even when the images differ in height.
for start in range(0, len(CHARTS), 2):
    columns = st.columns(2, gap="large")
    for column, (file, heading, takeaway) in zip(columns, CHARTS[start:start + 2]):
        with column:
            st.subheader(heading)
            image_path = ASSETS / file
            if image_path.exists():
                st.image(str(image_path))
            else:
                st.warning(f"Chart image not found: {file}")
            st.caption(takeaway)

st.info(
    "These are patterns in historical data, not proof of cause. For example, fiber optic "
    "customers may churn more because of price, competition or service quality, and this "
    "data cannot tell which."
)