# 📊 Telecom Customer Churn Analytics & Prediction

> An end-to-end Data Analytics & Machine Learning project that analyzes telecom customer behavior, identifies churn patterns, and predicts customer churn using multiple classification models.

---

## 📌 Project Overview

Customer churn is one of the biggest challenges in the telecom industry. Losing existing customers directly impacts revenue and business growth.

This project follows a complete **Data Analytics + Machine Learning workflow**, starting from raw data analysis to predictive modeling and interactive business dashboards.

The project aims to:

- Analyze customer demographics and service usage
- Identify factors influencing customer churn
- Build machine learning models to predict churn
- Create interactive Power BI dashboards for business insights
- Develop a reusable prediction pipeline

---

# 🚀 Project Workflow

```
Raw Dataset
     │
     ▼
Excel Analysis
     │
     ▼
SQL Business Analysis
     │
     ▼
Python Data Cleaning
     │
     ▼
Exploratory Data Analysis
     │
     ▼
Feature Engineering
     │
     ▼
Machine Learning Models
     │
     ▼
Hyperparameter Tuning
     │
     ▼
Model Evaluation
     │
     ▼
Prediction Pipeline
     │
     ▼
Power BI Dashboard
```

---

# 🛠 Tech Stack

### Data Analytics

- Microsoft Excel
- PostgreSQL
- Python

### Python Libraries

- Pandas
- NumPy
- Matplotlib
- Seaborn
- Scikit-learn
- Joblib

### Machine Learning

- Logistic Regression
- Decision Tree
- Random Forest
- K-Nearest Neighbors
- Gaussian Naive Bayes
- GridSearchCV

### Business Intelligence

- Microsoft Power BI

---

# 📂 Project Structure

```
Telecom-Customer-Churn-Prediction/

│
├── Data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── Notebook_1_Data_Cleaning.ipynb
│   ├── Notebook_2_SQL_Analysis.ipynb
│   ├── Notebook_3_Preprocessing.ipynb
│   ├── Notebook_4_Model_Building.ipynb
│   ├── Notebook_5_Model_Evaluation.ipynb
│   └── Notebook_6_Prediction_Pipeline.ipynb
│
├── models/
│   ├── random_forest.pkl
│   ├── logistic_regression.pkl
│   ├── scaler.pkl
│   ├── label_encoder.pkl
│   └── best_parameters.json
│
├── PowerBI/
│   └── Telecom_Churn_Dashboard.pbix
│
├── Documentation/
│   └── Project_Report.pdf
│
├── Images/
│
└── README.md
```

---

# 📈 Exploratory Data Analysis

The following analyses were performed:

- Customer Demographics
- Contract Analysis
- Internet Service Analysis
- Payment Method Analysis
- Customer Tenure Analysis
- Monthly Charges Analysis
- Churn Distribution
- Correlation Heatmap

---

# 🤖 Machine Learning Models

The following classification models were trained:

| Model | Test Accuracy |
|--------|--------------:|
| Logistic Regression | **80.20%** |
| Random Forest | **80.34%** |
| Decision Tree | **79.42%** |
| KNN | **75.87%** |
| Gaussian Naive Bayes | **65.58%** |

---

# 🎯 Hyperparameter Tuning

The best-performing models (Logistic Regression and Random Forest) were optimized using **GridSearchCV** with **5-Fold Cross Validation**.

Optimized Parameters:

- Logistic Regression
- Random Forest

---

# 📊 Model Evaluation

The final models were evaluated using:

- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix
- Classification Report
- ROC Curve
- ROC-AUC Score

### Final Model Performance

| Metric | Logistic Regression | Random Forest |
|---------|--------------------:|--------------:|
| Accuracy | 80.20% | **80.34%** |
| Precision | 64.98% | **66.44%** |
| Recall | **55.08%** | 52.41% |
| F1 Score | **59.62%** | 58.59% |
| ROC-AUC | 0.8409 | 0.8409 |

---

# 📊 Power BI Dashboard

Two interactive dashboards were developed.

### Dashboard 1

Executive Overview

Includes:

- Customer KPIs
- Revenue Analysis
- Contract Distribution
- Internet Service Analysis
- Payment Methods
- Churn Distribution

---

### Dashboard 2

Customer Insights

Includes:

- Customer Demographics
- Tenure Analysis
- Monthly Charges
- Service Analysis
- Churn by Contract
- Customer Behavior Analysis

---

# 💡 Key Business Insights

- Customers with **Month-to-Month contracts** have the highest churn rate.
- **Fiber Optic** customers are more likely to churn than DSL customers.
- Customers using **Electronic Check** exhibit higher churn.
- Customers with **longer tenure** demonstrate stronger loyalty.
- **Online Security** and **Tech Support** are associated with lower churn.
- Higher **Monthly Charges** increase churn probability.

---

# ✅ Business Recommendations

- Encourage customers to switch to long-term contracts.
- Promote automatic payment methods.
- Improve customer support for Fiber Optic users.
- Launch targeted retention campaigns for new customers.
- Bundle value-added services to improve customer satisfaction.
- Reward loyal customers through retention programs.

---

# 📸 Project Screenshots

## Power BI Dashboard

> Add dashboard screenshots here.

![Dashboard 1](Images/dashboard1.png)

![Dashboard 2](Images/dashboard2.png)

---

## Machine Learning

> Add ROC Curve, Confusion Matrix and Feature Importance.

---

# 🔮 Future Enhancements

- Deploy using Streamlit
- Integrate with Cloud Services
- Real-time Churn Prediction
- Customer Lifetime Value Prediction
- XGBoost / LightGBM Implementation
- Automated Data Pipeline

---

# ▶️ How to Run

### Clone the repository

```bash
git clone https://github.com/yourusername/Telecom-Customer-Churn-Prediction.git
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Open Jupyter Notebook

```bash
jupyter notebook
```

Run the notebooks sequentially.

---

# 👨‍💻 Author

**Ajay Elugubantla**

Aspiring Data Analyst | Data Science Enthusiast

### Skills

- Python
- SQL
- Excel
- Power BI
- Machine Learning
- Data Visualization

---

# ⭐ If you found this project useful, consider giving it a Star!