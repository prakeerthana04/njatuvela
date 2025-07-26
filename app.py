import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="🌾 Njatuvela Data Explorer", layout="wide")

theme = st.sidebar.radio("🌓 Select Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("<style>body {background-color: #0e1117; color: white;}</style>", unsafe_allow_html=True)

st.title("🌾 Njatuvela Data Explorer")
uploaded_file = st.sidebar.file_uploader("📁 Upload Excel file", type=["xlsx"])

@st.cache_data
def load_data(file):
    return pd.read_excel(file)

df = load_data(uploaded_file) if uploaded_file else load_data("njatuvella.xlsx")

st.success(f"✅ Data Loaded: {df.shape[0]} rows, {df.shape[1]} columns")

st.sidebar.header("🔍 Filter Options")

filter_columns = st.sidebar.multiselect("Select columns to filter", df.columns)
filtered_df = df.copy()
for col in filter_columns:
    unique_vals = df[col].dropna().unique().tolist()
    selected_vals = st.sidebar.multiselect(f"Filter values for {col}", unique_vals, default=unique_vals)
    filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

date_columns = df.select_dtypes(include=['datetime', 'object']).columns
date_column = st.sidebar.selectbox("📅 Date Column", ["None"] + list(date_columns))
if date_column != "None":
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    min_date = df[date_column].min()
    max_date = df[date_column].max()
    start_date, end_date = st.sidebar.date_input("Select date range", [min_date, max_date])
    if isinstance(start_date, pd.Timestamp) and isinstance(end_date, pd.Timestamp):
        filtered_df = filtered_df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]

search_term = st.sidebar.text_input("🔍 Global Search")
if search_term:
    filtered_df = filtered_df[filtered_df.astype(str).apply(
        lambda x: search_term.lower() in ' '.join(x).lower(), axis=1)]

st.markdown("### 📄 Filtered Data")
st.dataframe(filtered_df, use_container_width=True)

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(filtered_df)
st.download_button("⬇️ Download Filtered Data", csv, "filtered_njatuvella.csv", "text/csv")

st.markdown("### 📊 Summary Statistics")
st.dataframe(filtered_df.describe(include='all'), use_container_width=True)

st.markdown("### 📈 Charts & Visualization")

numeric_cols = filtered_df.select_dtypes(include=np.number).columns.tolist()
category_cols = filtered_df.select_dtypes(exclude=np.number).columns.tolist()

chart_type = st.selectbox("Choose Chart Type", ["Bar", "Line", "Pie"])

if chart_type == "Pie":
    pie_col = st.selectbox("Pie: Category", category_cols)
    pie_val = st.selectbox("Pie: Value", numeric_cols)
    fig = px.pie(filtered_df, names=pie_col, values=pie_val)
elif chart_type == "Bar":
    x_col = st.selectbox("Bar: X-axis", category_cols)
    y_col = st.selectbox("Bar: Y-axis", numeric_cols)
    fig = px.bar(filtered_df, x=x_col, y=y_col, color=x_col)
elif chart_type == "Line":
    x_col = st.selectbox("Line: X-axis", category_cols + numeric_cols)
    y_col = st.selectbox("Line: Y-axis", numeric_cols)
    fig = px.line(filtered_df, x=x_col, y=y_col)

st.plotly_chart(fig, use_container_width=True)

st.markdown("### 🗺️ Map View")
if {"Latitude", "Longitude"}.issubset(filtered_df.columns):
    map_df = filtered_df.dropna(subset=["Latitude", "Longitude"])
    st.map(map_df[["Latitude", "Longitude"]])
elif "Location" in filtered_df.columns:
    st.info("🧭 Convert 'Location' column to Latitude/Longitude for map view support.")

st.markdown("### 🔄 Pivot Table")

pivot_rows = st.multiselect("Rows", df.columns)
pivot_columns = st.multiselect("Columns", df.columns)
pivot_values = st.multiselect("Values", numeric_cols)

if pivot_rows and pivot_values:
    try:
        pivot_table = pd.pivot_table(
            filtered_df,
            index=pivot_rows,
            columns=pivot_columns if pivot_columns else None,
            values=pivot_values,
            aggfunc='sum',
            fill_value=0
        )
        st.dataframe(pivot_table, use_container_width=True)
    except Exception as e:
        st.error(f"Error creating pivot table: {e}")
else:
    st.info("Select at least one row and one value column for pivot table.")
