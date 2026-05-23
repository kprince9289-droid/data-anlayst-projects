# ============================================
# LOAN DEFAULT PREDICTION PROJECT (WEB APP)
# Complete End-to-End Upgraded Python Code
# ============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import io

from sklearn.model_selection import train_test_split
# Using standard LaTeX notation for ML components: features $X$, target $y$
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Set page styling configuration
st.set_page_config(page_title="Loan Default Dashboard", layout="wide")
sns.set_theme(style="whitegrid")  # Set standard neat plot grids

st.title("🏦 Advanced Loan Default Analytics & Prediction Platform")
st.write("An end-to-end interactive intelligence dashboard for evaluating credit default risks using Machine Learning.")

# ============================================
# Step 1: Load Dataset
# ============================================
st.sidebar.header("📁 Data Source Configuration")
file_path = r"C:\Users\Hp\Downloads\loan_default_dataset.csv"

try:
    df = pd.read_csv(file_path)
    st.sidebar.success("Dataset loaded successfully from Downloads!")
except Exception as e:
    st.sidebar.error(f"Error loading CSV file: {e}")
    st.stop()

# ============================================
# Step 2: Data Cleaning & Feature Engineering
# ============================================
# Remove duplicate records
df.drop_duplicates(inplace=True)

# Cache unique categories before dropping or transforming columns
if 'EmploymentStatus' in df.columns:
    unique_employment_types = sorted(list(df['EmploymentStatus'].dropna().unique()))
else:
    unique_employment_types = ["Employed", "Self-Employed", "Unemployed"]

# Remove non-predictive high-cardinality identifier
if 'CustomerID' in df.columns:
    df.drop('CustomerID', axis=1, inplace=True)

# Separate numeric and categorical series names
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
if 'Default' in numeric_cols:
    numeric_cols.remove('Default')  # Exclude target column from imputation matrix
categorical_cols = df.select_dtypes(include='object').columns.tolist()

# Handle missing values using imputation strategies
if len(numeric_cols) > 0:
    num_imputer = SimpleImputer(strategy='median')
    df[numeric_cols] = num_imputer.fit_transform(df[numeric_cols])

if len(categorical_cols) > 0:
    cat_imputer = SimpleImputer(strategy='most_frequent')
    df[categorical_cols] = cat_imputer.fit_transform(df[categorical_cols])

# Feature Engineering: Financial Risk Ratios
df['DTI_Ratio'] = df['LoanAmount'] / (df['Income'] + 1)
df['EMI_Burden'] = df['EMI'] / (df['Income'] + 1)

# Categorical Label Encoding Pipeline
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le

# Split features ($X$) and target target vector ($y$)
X = df.drop('Default', axis=1)
y = df['Default'].astype(int)

# Train-Test Split Matrix Validation Configuration
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# ============================================
# Step 3: Model Building (Cached for Speed)
# ============================================
@st.cache_resource
def train_ml_models(X_tr, y_tr):
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(X_tr, y_tr)

    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_tr, y_tr)
    return lr, rf


lr_model, rf_model = train_ml_models(X_train, y_train)

# ============================================
# Step 4: UI Navigation Structure
# ============================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Data Summary",
    "📊 Well-Organized Visualizations",
    "🎯 Model Evaluation",
    "🔮 Risk Inference Engine"
])

# ---- TAB 1: DATA OVERVIEW ----
with tab1:
    st.header("Dataset Descriptive Overview")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Client Records", df.shape[0])
    m2.metric("Total Model Features Evaluated", df.shape[1] - 1)
    m3.metric("Observed Default Rate", f"{(y.sum() / len(y) * 100):.2f}%")

    st.subheader("Data Preview Sample (First 5 Rows)")
    st.dataframe(df.head())

    st.subheader("Technical Column Architecture")
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

# ---- TAB 2: WELL-ORGANIZED VISUALIZATIONS ----
with tab2:
    st.header("Exploratory Data Analysis Dashboard")
    st.write("Visualizations are structured into categorical modules to identify risk relationships.")

    # Category 1: Target and Categorical Breakdown
    st.subheader("1. Core Risk Class Distribution")
    v_col1, v_col2 = st.columns(2)

    with v_col1:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.countplot(x=y, ax=ax, palette="coolwarm")
        ax.set_title("Distribution of Loan Defaults (0 = Paid, 1 = Defaulted)", fontsize=10)
        ax.set_xlabel("Default Class Status")
        st.pyplot(fig)
        plt.close(fig)

    with v_col2:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        # Grouped by Employment Status representation
        sns.countplot(x='EmploymentStatus', hue=y, data=df, ax=ax, palette="Set2")
        ax.set_title("Default Distribution across Employment Status Index", fontsize=10)
        ax.set_xlabel("Employment Status (Encoded)")
        st.pyplot(fig)
        plt.close(fig)

    # Category 2: Financial Profile & Distributions
    st.markdown("---")
    st.subheader("2. Financial Capital Profiles")
    v_col3, v_col4 = st.columns(2)

    with v_col3:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.histplot(df['Income'], kde=True, ax=ax, color="#2b5c8f")
        ax.set_title("Customer Annual Income Distribution Profile", fontsize=10)
        st.pyplot(fig)
        plt.close(fig)

    with v_col4:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        sns.boxplot(x=y, y='CreditScore', data=df, ax=ax, palette="vlag")
        ax.set_title("Credit Score Distribution vs Default Risk Outcome", fontsize=10)
        st.pyplot(fig)
        plt.close(fig)

    # Category 3: Multivariant & Correlation
    st.markdown("---")
    st.subheader("3. Risk Covariation & Correlations")
    v_col5, v_col6 = st.columns([1.2, 1])

    with v_col5:
        fig, ax = plt.subplots(figsize=(8, 5))
        corr_matrix = df.corr(numeric_only=True)
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", ax=ax, annot_kws={"size": 8})
        ax.set_title("Full Linear Correlation Metric Heatmap Matrix", fontsize=11)
        st.pyplot(fig)
        plt.close(fig)

    with v_col6:
        fig, ax = plt.subplots(figsize=(6, 4.5))
        sns.scatterplot(x='Income', y='LoanAmount', hue=y, data=df, ax=ax, alpha=0.7, palette="tab10")
        ax.set_title("Loan Request Size vs Annual Income Scatterplot", fontsize=10)
        st.pyplot(fig)
        plt.close(fig)

# ---- TAB 3: MODEL PERFORMANCE ----
with tab3:
    st.header("Machine Learning Predictive Model Reports")
    selected_alg = st.selectbox("Select Trained Model Engine:", ["Random Forest Classifier", "Logistic Regression"])

    if selected_alg == "Logistic Regression":
        active_preds = lr_model.predict(X_test)
        auc_score = roc_auc_score(y_test, active_preds)
        accuracy = accuracy_score(y_test, active_preds)
        report_dict = classification_report(y_test, active_preds, output_dict=True)
    else:
        active_preds = rf_model.predict(X_test)
        auc_score = roc_auc_score(y_test, active_preds)
        accuracy = accuracy_score(y_test, active_preds)
        report_dict = classification_report(y_test, active_preds, output_dict=True)

    ev1, ev2 = st.columns(2)
    ev1.metric(f"Engine Accuracy Score", f"{accuracy * 100:.2f}%")
    ev2.metric("Calculated area under ROC-AUC curve", f"{auc_score:.4f}")

    st.subheader("Comprehensive Classification Report Grid Matrix")
    st.dataframe(pd.DataFrame(report_dict).transpose())

    if selected_alg == "Random Forest Classifier":
        st.subheader("Structural Feature Importance Breakdown (Top Ranked Key Risk Factors)")
        fi_df = pd.DataFrame({'Feature': X.columns, 'Importance': rf_model.feature_importances_})
        fi_df = fi_df.sort_values(by='Importance', ascending=False)

        fig, ax = plt.subplots(figsize=(10, 4.5))
        sns.barplot(x='Importance', y='Feature', data=fi_df.head(10), ax=ax, palette="magma")
        ax.set_title("Top 10 Most Predictive Features determining Risk Defaults", fontsize=11)
        st.pyplot(fig)
        plt.close(fig)

# ---- TAB 4: RISK INFERENCE ENGINE ----
with tab4:
    st.header("Real-Time Application Risk Underwriting Engine")
    st.write("Modify applicant parameters below to immediately score potential credit default likelihood.")

    col_inputs_left, col_inputs_right = st.columns(2)

    with col_inputs_left:
        user_age = st.number_input("Applicant Age Horizon", min_value=18, max_value=90, value=35)
        user_income = st.number_input("Verifiable Total Annual Income ($)", min_value=5000, max_value=1000000,
                                      value=50000)
        user_loan = st.number_input("Requested Principal Loan Amount ($)", min_value=2000, max_value=2500000,
                                    value=200000)
        user_credit = st.slider("Bureau Registered Credit Score", min_value=300, max_value=850, value=700)

    with col_inputs_right:
        user_emp = st.selectbox("Applicant Employment Track Status", unique_employment_types)
        user_existing = st.number_input("Active Concurrent Credit Lines/Loans Count", min_value=0, max_value=15,
                                        value=2)
        user_term = st.selectbox("Amortization Payback Duration Term (Months)", [12, 24, 36, 48, 60], index=2)
        user_emi = st.number_input("Computed Scheduled Monthly Loan EMI ($)", min_value=10, max_value=100000,
                                   value=8000)

    # Calculate engineered values identical to training parameters pipeline
    calc_dti = user_loan / (user_income + 1)
    calc_emi_burden = user_emi / (user_income + 1)

    # Safe encoded lookup mapping for Employment Status selection mapping back to target arrays
    if 'EmploymentStatus' in label_encoders:
        encoded_employment_value = label_encoders['EmploymentStatus'].transform([user_emp])[0]
    else:
        encoded_employment_value = 0

    # Build evaluation row vectors matching feature arrays assignment sequences exactly
    raw_inference_dict = {
        'Age': [user_age],
        'Income': [user_income],
        'LoanAmount': [user_loan],
        'CreditScore': [user_credit],
        'EmploymentStatus': [encoded_employment_value],
        'ExistingLoans': [user_existing],
        'LoanTerm': [user_term],
        'EMI': [user_emi],
        'DTI_Ratio': [calc_dti],
        'EMI_Burden': [calc_emi_burden]
    }

    inference_df = pd.DataFrame(raw_inference_dict)
    inference_df = inference_df[X.columns]  # Enforce column layout match

    if st.button("Execute Quantitative Underwriting Risk Scoring", type="primary"):
        class_prediction = rf_model.predict(inference_df)
        probability_score = rf_model.predict_proba(inference_df)[0][1]

        st.markdown("---")
        st.subheader("Underwriting Risk Result Verdict:")
        if class_prediction[0] == 1:
            st.error(
                f"🚨 **High Credit Risk Alert:** System advises against automatic acquisition. The model forecasts a high risk of **DEFAULT**. (Probability: {probability_score * 100:.1f}%)")
        else:
            st.success(
                f"✅ **Credit Application Cleared:** System assesses acceptable risk. Candidate is **NOT likely to default**. (Risk Exposure Probability: {probability_score * 100:.1f}%)")