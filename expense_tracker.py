import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# DATABASE SETUP & UTILITIES
# ---------------------------------------------------------
DB_FILE = "expenses.db"


def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        )
    ''')
    # Create budget table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            amount REAL
        )
    ''')
    conn.commit()
    conn.close()


def add_expense(date, category, amount, description):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (date, category, amount, description)
        VALUES (?, ?, ?, ?)
    ''', (date, category, amount, description))
    conn.commit()
    conn.close()


def get_all_expenses():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    return df


def set_budget(category, amount):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO budgets (category, amount)
        VALUES (?, ?)
    ''', (category, amount))
    conn.commit()
    conn.close()


def get_budgets():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budgets")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


# Initialize database right away
init_db()

# ---------------------------------------------------------
# STREAMLIT USER INTERFACE DESIGN
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Expense Tracker", page_icon="💰", layout="wide")

st.title("💰 Smart Expense Tracker & Budget Dashboard")
st.markdown("Track your day-to-day spending, set strict monthly budgets, and analyze your financial habits.")
st.markdown("---")

# Predefined categories
CATEGORIES = ["Food & Dining", "Rent & Bills", "Transportation", "Shopping", "Entertainment", "Medical", "Others"]

# Sidebar configuration: Input Section
with st.sidebar:
    st.header("📥 Log New Expense")
    exp_date = st.date_input("Date of Transaction", datetime.now())
    exp_category = st.selectbox("Category", CATEGORIES)
    exp_amount = st.number_input("Amount (₹)", min_value=1.0, step=10.0)
    exp_desc = st.text_input("Short Description", placeholder="e.g., Grocery shopping")

    if st.button("Add Expense", use_container_width=True):
        add_expense(exp_date.strftime("%Y-%m-%d"), exp_category, exp_amount, exp_desc)
        st.success("Expense logged successfully!")
        st.rerun()

    st.markdown("---")
    st.header("🎯 Set Monthly Budgets")
    budget_cat = st.selectbox("Select Target Category", CATEGORIES, key="budget_cat")
    budget_amt = st.number_input("Budget Limit (₹)", min_value=0.0, step=100.0)

    if st.button("Save Budget Limit", use_container_width=True):
        set_budget(budget_cat, budget_amt)
        st.success(f"Budget updated for {budget_cat}!")
        st.rerun()

# Main Dashboard Window
df_expenses = get_all_expenses()
budgets = get_budgets()

# Convert date column to datetime type for seamless filtering
if not df_expenses.empty:
    df_expenses['date'] = pd.to_datetime(df_expenses['date'])
    df_expenses['Month'] = df_expenses['date'].dt.strftime('%B %Y')

    # Quick filter for current month analysis
    current_month = datetime.now().strftime('%B %Y')
    df_current = df_expenses[df_expenses['Month'] == current_month]
else:
    df_current = pd.DataFrame()

# KPI Metric Summary Blocks
st.subheader(f"📊 Summary Financial Cards ({datetime.now().strftime('%B %Y')})")
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    total_spent = df_current['amount'].sum() if not df_current.empty else 0.0
    st.metric(label="Total Outflow This Month", value=f"₹{total_spent:,.2f}")

with kpi2:
    total_budget = sum(budgets.values())
    st.metric(label="Total Allocated Budget", value=f"₹{total_budget:,.2f}")

with kpi3:
    remaining_balance = total_budget - total_spent
    if remaining_balance < 0:
        st.metric(label="Net Savings Deficit", value=f"₹{remaining_balance:,.2f}", delta="-Budget Breached!",
                  delta_color="inverse")
    else:
        st.metric(label="Safe-to-Spend Balance", value=f"₹{remaining_balance:,.2f}", delta="+Within Limits")

st.markdown("---")

# Visual Analytics Graphs & Breakdown Section
if not df_expenses.empty:
    col_graph1, col_graph2 = st.columns(2)

    with col_graph1:
        st.markdown("### 🍕 Spending Distribution by Category")
        cat_totals = df_expenses.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(cat_totals, values="amount", names="category", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graph2:
        st.markdown("### ⚠️ Budget vs. Actual Expenditure Variance")
        # Build comparative dataframe
        comparison_records = []
        for cat in CATEGORIES:
            actual = df_current[df_current['category'] == cat]['amount'].sum() if not df_current.empty else 0
            allocated = budgets.get(cat, 0.0)
            comparison_records.append({"Category": cat, "Actual Spent": actual, "Budget Limit": allocated})

        df_comp = pd.DataFrame(comparison_records)

        fig_bar = px.bar(df_comp, x="Category", y=["Actual Spent", "Budget Limit"],
                         bgroupmode="group", title="",
                         labels={"value": "Amount (₹)", "variable": "Metrics"},
                         color_discrete_map={"Actual Spent": "#E74C3C", "Budget Limit": "#2ECC71"})
        st.plotly_chart(fig_bar, use_container_width=True)

        # Budget Warning Indicators Trigger
        for index, row in df_comp.iterrows():
            if row['Actual Spent'] > row['Budget Limit'] > 0:
                st.warning(
                    f"🚨 **{row['Category']}** threshold breached by **₹{row['Actual Spent'] - row['Budget Limit']:.2f}**!")

    # Tabular Ledger View
    st.markdown("### 📜 Detailed Historical Transaction Ledger")
    # Clean output formatting for presentation dataframe
    df_display = df_expenses.copy()
    df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
    st.dataframe(df_display[["date", "category", "amount", "description"]], use_container_width=True)

    # Download Report Button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Monthly Ledger Report to CSV",
        data=csv,
        file_name="financial_expense_statement.csv",
        mime="text/csv"
    )
else:
    st.info("💡 Get started by adding your first expense transaction entry using the left side control panel panel!")