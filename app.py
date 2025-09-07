# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data_generator import generate_dummy_orders
from datetime import timedelta

st.set_page_config(page_title="Blinkit Ops Dashboard", layout="wide", initial_sidebar_state="expanded")
st.title("Blinkit — Monthly Sales & Delivery Performance")

@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, parse_dates=["Order_Date"])
    else:
        df = generate_dummy_orders(n=15000)
    return df

uploaded = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"])
df = load_data(uploaded)

# preprocessing
df["Order_Month"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
min_date, max_date = df["Order_Date"].min(), df["Order_Date"].max()

# sidebar filters
st.sidebar.markdown("### Filters")
date_range = st.sidebar.date_input("Order date range", [min_date.date(), max_date.date()])
city_sel = st.sidebar.multiselect("Cities", sorted(df["City"].unique()), default=sorted(df["City"].unique()))
product_sel = st.sidebar.multiselect("Products (optional)", sorted(df["Product"].unique()), default=None)

# apply filters
start_dt = pd.to_datetime(date_range[0])
end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
mask = (df["Order_Date"] >= start_dt) & (df["Order_Date"] <= end_dt) & (df["City"].isin(city_sel))
if product_sel:
    mask &= df["Product"].isin(product_sel)
dff = df[mask].copy()

# KPIs
total_sales = dff["Sales"].sum()
avg_delivery = dff["Delivery_Time_min"].mean() if len(dff)>0 else 0
orders_count = len(dff)
# MoM change (last month vs previous)
monthly = dff.groupby("Order_Month").agg({"Sales":"sum"}).reset_index().sort_values("Order_Month")
last = monthly.iloc[-1]["Sales"] if len(monthly)>0 else 0
prev = monthly.iloc[-2]["Sales"] if len(monthly)>1 else 0
mom_delta = (last - prev)/prev*100 if prev>0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales (₹)", f"{total_sales:,.0f}")
col2.metric("Avg Delivery (min)", f"{avg_delivery:.1f}")
col3.metric("Orders", f"{orders_count}")
col4.metric("MoM Sales Δ", f"{mom_delta:.1f}%", delta_color="normal")

st.markdown("---")
# Charts: monthly sales line
with st.container():
    st.subheader("Monthly Sales & Avg Delivery")
    m_sales = dff.groupby("Order_Month").agg({"Sales":"sum","Delivery_Time_min":"mean"}).reset_index()
    if m_sales.empty:
        st.info("No data for selected filters.")
    else:
        fig1 = px.line(m_sales, x="Order_Month", y="Sales", title="Monthly Sales (₹)", markers=True)
        fig2 = px.line(m_sales, x="Order_Month", y="Delivery_Time_min", title="Avg Delivery Time (min)", markers=True)
        left, right = st.columns(2)
        left.plotly_chart(fig1, use_container_width=True)
        right.plotly_chart(fig2, use_container_width=True)

# City-wise
st.subheader("City-wise Performance")
city_stats = dff.groupby("City").agg(Sales=("Sales","sum"), Avg_Delivery=("Delivery_Time_min","mean"), Orders=("Order_ID","count")).reset_index().sort_values("Sales", ascending=False)
fig_city_sales = px.bar(city_stats, x="City", y="Sales", title="Sales by City (₹)", text_auto=True)
fig_city_delivery = px.bar(city_stats, x="City", y="Avg_Delivery", title="Avg Delivery by City (min)", text_auto=True)
c1, c2 = st.columns(2)
c1.plotly_chart(fig_city_sales, use_container_width=True)
c2.plotly_chart(fig_city_delivery, use_container_width=True)

# Scatter: Sales vs Delivery (identify tradeoffs)
st.subheader("Sales vs Avg Delivery — cities (size = orders)")
fig_scatter = px.scatter(city_stats, x="Avg_Delivery", y="Sales", size="Orders", hover_name="City",
                         labels={"Avg_Delivery":"Avg Delivery (min)", "Sales":"Total Sales (₹)"}, title="City trade-off: delivery vs sales")
st.plotly_chart(fig_scatter, use_container_width=True)

# Data table + download
st.subheader("Underlying Orders (filtered)")
st.dataframe(dff.sort_values("Order_Date", ascending=False).reset_index(drop=True), use_container_width=True)
csv = dff.to_csv(index=False).encode('utf-8')
st.download_button("Download filtered CSV", csv, "blinkit_filtered.csv", "text/csv")
