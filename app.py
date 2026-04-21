import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os, re

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SpendSense",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSV_FILE = "expenses.csv"

# ─────────────────────────────────────────────
# AUTO-CATEGORIZATION
# ─────────────────────────────────────────────
KEYWORDS = {
    "🍔 Food":          ["zomato", "swiggy", "restaurant", "cafe", "pizza", "biryani",
                         "burger", "tea", "coffee", "lunch", "dinner", "breakfast",
                         "chai", "food", "meal", "snack", "juice", "bakery"],
    "🚗 Transport":     ["uber", "ola", "petrol", "bus", "metro", "rapido", "auto",
                         "taxi", "fuel", "train", "flight", "toll", "parking"],
    "🎮 Entertainment": ["netflix", "spotify", "movie", "game", "youtube", "prime",
                         "hotstar", "concert", "cricket", "sports", "disney", "ticket"],
    "🛒 Shopping":      ["amazon", "flipkart", "meesho", "clothes", "shoes", "myntra",
                         "shirt", "jeans", "purchase", "buy", "mall", "retail", "store"],
    "🏥 Health":        ["pharmacy", "doctor", "gym", "medicine", "hospital", "clinic",
                         "chemist", "health", "dental", "yoga", "tablets", "medical"],
    "🔌 Utilities":     ["electricity", "wifi", "water", "rent", "recharge", "mobile",
                         "internet", "gas", "maintenance", "bill", "broadband"],
    "📚 Education":     ["book", "course", "udemy", "college", "tuition", "stationery",
                         "pen", "notebook", "exam", "fee", "class", "study"],
}

ALL_CATS = list(KEYWORDS.keys()) + ["📦 Other"]

def auto_categorize(description: str) -> str:
    """Match description keywords to a spending category."""
    desc = description.lower()
    for category, keywords in KEYWORDS.items():
        if any(kw in desc for kw in keywords):
            return category
    return "📦 Other"

# ─────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    """Load expenses from CSV. Return empty DataFrame if file doesn't exist."""
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df["Date"] = pd.to_datetime(df["Date"], format="mixed")
        return df
    return pd.DataFrame(columns=["Date", "Description", "Amount", "Category"])

def save_data(df: pd.DataFrame):
    """Save DataFrame to CSV."""
    df.to_csv(CSV_FILE, index=False)

def add_expense(description: str, amount: float, exp_date: date, category: str):
    """Append a new expense row and save."""
    df = load_data()
    new_row = pd.DataFrame([{
        "Date":        exp_date,
        "Description": description,
        "Amount":      amount,
        "Category":    category
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)

def delete_expense(index: int):
    """Drop a row by index and save."""
    df = load_data()
    df = df.drop(index=index).reset_index(drop=True)
    save_data(df)

# ─────────────────────────────────────────────
# INSIGHTS ENGINE
# ─────────────────────────────────────────────
def generate_insights(df: pd.DataFrame, monthly_budget: float) -> list:
    """Generate rule-based financial tips from spending data."""
    insights = []

    if df.empty:
        return ["Add some expenses to see insights! 📝"]

    total           = df["Amount"].sum()
    category_totals = df.groupby("Category")["Amount"].sum()

    # Budget status
    if total > monthly_budget:
        over = total - monthly_budget
        insights.append(f"🚨 Over budget by **₹{over:,.0f}**! Cut back immediately.")
    else:
        remaining = monthly_budget - total
        pct_used  = (total / monthly_budget) * 100
        insights.append(f"✅ **₹{remaining:,.0f}** remaining this month ({pct_used:.0f}% used).")

    # Category-level tips
    for cat, amt in category_totals.items():
        pct = (amt / total) * 100
        if "Food" in cat and pct > 35:
            savings = amt * 0.3
            insights.append(
                f"🍔 Food spending is **{pct:.0f}%** of total (₹{amt:,.0f}). "
                f"Try meal prepping — could save ₹{savings:,.0f}/month."
            )
        if "Entertainment" in cat and pct > 20:
            insights.append(
                f"🎮 Entertainment is **{pct:.0f}%** (₹{amt:,.0f}). "
                f"Audit subscriptions — cancel ones you rarely use."
            )
        if "Shopping" in cat and pct > 25:
            insights.append(
                f"🛒 Shopping is **{pct:.0f}%** (₹{amt:,.0f}). "
                f"Try the 48-hour rule before non-essential purchases."
            )
        if "Transport" in cat and pct > 20:
            insights.append(
                f"🚗 Transport is **{pct:.0f}%** (₹{amt:,.0f}). "
                f"A monthly metro pass could reduce costs significantly."
            )

    # Top category
    top_cat = category_totals.idxmax()
    insights.append(
        f"📊 Your biggest spend is **{top_cat}** at ₹{category_totals[top_cat]:,.0f}."
    )

    return insights

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
def pie_chart(df: pd.DataFrame):
    """Donut pie chart — spending by category."""
    cat_totals = df.groupby("Category")["Amount"].sum().reset_index()
    fig = px.pie(
        cat_totals,
        values="Amount",
        names="Category",
        title="Spending by Category",
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.4
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
    return fig

def bar_chart(df: pd.DataFrame):
    """Bar chart — weekly spending trend."""
    df = df.copy()
    df["Week"] = pd.to_datetime(df["Date"], format="mixed").dt.to_period("W").astype(str)
    weekly = df.groupby("Week")["Amount"].sum().reset_index()
    fig = px.bar(
        weekly,
        x="Week",
        y="Amount",
        title="Weekly Spending Trend",
        color="Amount",
        color_continuous_scale="Blues",
        labels={"Amount": "₹ Spent"}
    )
    fig.update_layout(coloraxis_showscale=False, margin=dict(t=40, b=0))
    return fig

def line_chart(df: pd.DataFrame):
    """Line chart — month-over-month spending."""
    df = df.copy()
    df["Month"] = pd.to_datetime(df["Date"], format="mixed").dt.to_period("M").astype(str)
    monthly = df.groupby("Month")["Amount"].sum().reset_index()
    fig = px.line(
        monthly,
        x="Month",
        y="Amount",
        title="Monthly Spending",
        markers=True,
        labels={"Amount": "₹ Spent"},
        color_discrete_sequence=["#22c55e"]
    )
    fig.update_layout(margin=dict(t=40, b=0))
    return fig

# ─────────────────────────────────────────────
# SIDEBAR — INPUT FORM
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("💰 SpendSense")
    st.caption("Personal Finance Tracker")
    st.divider()

    st.subheader("➕ Add Expense")

    description = st.text_input(
        "Description",
        placeholder="e.g. Zomato biryani"
    )

    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0,
        step=10.0,
        format="%.2f"
    )

    exp_date = st.date_input("Date", value=date.today())

    # Auto-detect category, allow manual override
    detected = auto_categorize(description) if description else "📦 Other"

    if description:
        st.caption(f"Auto-detected: **{detected}**")

    category = st.selectbox(
        "Category",
        options=ALL_CATS,
        index=ALL_CATS.index(detected) if detected in ALL_CATS else len(ALL_CATS) - 1,
        help="Automatically detected from description. You can change it."
    )

    if st.button("Add Expense", use_container_width=True, type="primary"):
        if description.strip() and amount > 0:
            add_expense(description.strip(), amount, exp_date, category)
            st.success("✅ Expense added!")
            st.rerun()
        else:
            st.error("Please fill in description and amount.")

    st.divider()

    # Budget control
    st.subheader("🎯 Monthly Budget")
    monthly_budget = st.number_input(
        "Set Budget (₹)",
        min_value=0.0,
        value=10000.0,
        step=500.0,
        format="%.0f"
    )

    # Export button
    st.divider()
    df_export = load_data()
    if not df_export.empty:
        csv_data = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export to CSV",
            data=csv_data,
            file_name="my_expenses.csv",
            mime="text/csv",
            use_container_width=True
        )

# ─────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────
df = load_data()

st.title("📊 My Expense Dashboard")

if df.empty:
    st.info("No expenses yet. Add your first one from the sidebar! 👈")
    st.stop()

# ── KPI Cards ────────────────────────────────
total_spent  = df["Amount"].sum()
avg_daily    = df.groupby("Date")["Amount"].sum().mean()
num_entries  = len(df)
top_category = df.groupby("Category")["Amount"].sum().idxmax()
budget_left  = monthly_budget - total_spent

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💸 Total Spent",      f"₹{total_spent:,.0f}")
c2.metric("📅 Avg Daily Spend",  f"₹{avg_daily:,.0f}")
c3.metric("🧾 Transactions",     num_entries)
c4.metric("🏆 Top Category",     top_category)
c5.metric(
    "🎯 Budget Left",
    f"₹{budget_left:,.0f}",
    delta=f"{'Over' if budget_left < 0 else 'Under'} budget",
    delta_color="inverse"
)

st.divider()

# ── Charts ───────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.plotly_chart(pie_chart(df), use_container_width=True)
with col_b:
    st.plotly_chart(bar_chart(df), use_container_width=True)

st.plotly_chart(line_chart(df), use_container_width=True)

st.divider()

# ── Smart Insights ───────────────────────────
st.subheader("💡 Smart Insights")
insights = generate_insights(df, monthly_budget)
for tip in insights:
    st.markdown(f"- {tip}")

st.divider()

# ── Expense Table ────────────────────────────
st.subheader("📋 All Expenses")

col_filter, col_sort = st.columns([3, 1])
with col_filter:
    selected_cats = st.multiselect(
        "Filter by Category",
        options=df["Category"].unique().tolist(),
        default=df["Category"].unique().tolist()
    )
with col_sort:
    sort_by = st.selectbox("Sort by", ["Date ↓", "Date ↑", "Amount ↓", "Amount ↑"])

# Apply filter
filtered_df = df[df["Category"].isin(selected_cats)].copy()

# Apply sort
sort_map = {
    "Date ↓":   ("Date",   False),
    "Date ↑":   ("Date",   True),
    "Amount ↓": ("Amount", False),
    "Amount ↑": ("Amount", True),
}
sort_col, sort_asc = sort_map[sort_by]
filtered_df = filtered_df.sort_values(sort_col, ascending=sort_asc)

# Render rows
if filtered_df.empty:
    st.info("No expenses match the selected filters.")
else:
    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} expenses | Total: ₹{filtered_df['Amount'].sum():,.0f}**")
    st.write("")

    for i, row in filtered_df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 4, 2, 2, 1])
        c1.write(str(row["Date"])[:10])
        c2.write(row["Description"])
        c3.write(row["Category"])
        c4.write(f"₹{row['Amount']:,.2f}")
        if c5.button("🗑️", key=f"del_{i}", help="Delete this expense"):
            delete_expense(i)
            st.rerun()