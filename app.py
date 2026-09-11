import streamlit as st
import pandas as pd
from ingestion import handle_file_upload
from schema_mapper import render_mapping_ui, apply_mapping
from cleaning import clean_data, render_quality_report
from transform import transform_data
from metrics import render_metrics
import charts
from report import render_report_tab
import ml_engine

# 1. Page Configuration
st.set_page_config(page_title="Dynamic Sales Dashboard", layout="wide")

st.title("📊 Dynamic Sales Dashboard")
st.markdown("Upload any sales CSV file, map your columns, and instantly get insights!")



# Initialize session state variables
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "file_hash" not in st.session_state:
    st.session_state.file_hash = None
if "mapping" not in st.session_state:
    st.session_state.mapping = None
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None
if "quality_report" not in st.session_state:
    st.session_state.quality_report = None

# 2. Upload Stage
file_hash, raw_df = handle_file_upload()

# Handle new file upload
if file_hash and file_hash != st.session_state.file_hash:
    st.session_state.file_hash = file_hash
    st.session_state.raw_df = raw_df
    # Reset downstream state for new file
    st.session_state.mapping = None
    st.session_state.cleaned_df = None
    st.session_state.quality_report = None
    if "best_guess_mapping" in st.session_state:
        del st.session_state.best_guess_mapping

# If no file is loaded, stop here
if st.session_state.raw_df is None:
    st.stop()

# 3. Schema Mapping Stage
if st.session_state.mapping is None:
    st.divider()
    confirmed_mapping = render_mapping_ui(st.session_state.raw_df)
    
    if confirmed_mapping:
        st.session_state.mapping = confirmed_mapping
        st.rerun()
    else:
        st.stop() # Wait for user to confirm mapping

# 4. Cleaning & Transformation Stage
if st.session_state.cleaned_df is None:
    # Rename columns to canonical names
    mapped_df = apply_mapping(st.session_state.raw_df, st.session_state.mapping)
    
    # Clean data (coerce types, remove duplicates, etc.)
    cleaned_df, quality_report = clean_data(mapped_df, st.session_state.mapping)
    
    # Apply transformations (feature engineering)
    transformed_df = transform_data(cleaned_df)
    
    st.session_state.cleaned_df = transformed_df
    st.session_state.quality_report = quality_report

# 5. Dashboard Rendering Stage
st.divider()

# Show Data Quality Report
render_quality_report(st.session_state.quality_report)

st.divider()

# Get the ready-to-use dataframe
df = st.session_state.cleaned_df

# Sidebar Filters
st.sidebar.header("Dashboard Filters")

filtered_df = df.copy()

# Fix Category Filter (Ensuring native streamlit behavior)
if "category" in df.columns:
    available_categories = df["category"].dropna().unique()
    if len(available_categories) > 0:
        selected_categories = st.sidebar.multiselect("Select Category", available_categories, available_categories)
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]

# Safety check: Stop the app if filters are empty
if filtered_df.empty:
    st.warning("⚠️ No data matches the current filters. Please adjust your selection.")
    st.stop()

# Render Top-Level KPIs
render_metrics(filtered_df)

st.divider()

# Dashboard Tabs (Exactly 4 Tabs)
tab1, tab2, tab3, tab4 = st.tabs(["📈 Sales & Trends", "🌍 Geography & Customers", "📥 Data & Export", "🤖 Predictive Insights"])

with tab1:
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        charts.render_monthly_sales_trend(filtered_df)

    with chart_col2:
        charts.render_sales_by_subcategory(filtered_df)

    st.divider()
    charts.render_pareto_chart(filtered_df)

with tab2:
    adv_col1, adv_col2 = st.columns(2)

    with adv_col1:
        charts.render_sales_by_segment(filtered_df)

    with adv_col2:
        charts.render_sales_map(filtered_df)

with tab3:
    render_report_tab(filtered_df)

with tab4:
    st.header("🤖 Predictive Insights")
    st.markdown("Leverage Machine Learning to forecast future revenue and identify at-risk customers.")
    
    # Section 1: Forecasting
    st.divider()
    st.subheader("🔮 30-Day Revenue Forecast")
    
    forecast_days = st.slider("Forecast Horizon (Days)", min_value=15, max_value=90, value=30, step=5)
    
    with st.spinner("Training forecasting model..."):
        forecast_df = ml_engine.forecast_sales(filtered_df, forecast_days=forecast_days)
        
    charts.plot_sales_forecast(forecast_df)
    
    # Section 2: Churn
    st.divider()
    st.subheader("⚠️ Customer Churn & Retention")
    
    with st.spinner("Training churn prediction model..."):
        churn_df, importances_df = ml_engine.train_churn_model(filtered_df)
        
    if churn_df is not None:
        charts.plot_churn_risk(churn_df, importances_df)
        
        st.write("### High-Risk Customers")
        high_risk_threshold = st.slider("Churn Probability Threshold (%)", min_value=50, max_value=99, value=70, step=5)
        
        high_risk_df = churn_df[churn_df['Churn Probability'] >= high_risk_threshold].sort_values(by='Churn Probability', ascending=False)
        
        if not high_risk_df.empty:
            st.dataframe(high_risk_df, use_container_width=True)
            
            csv_data = high_risk_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download High-Risk Customers",
                data=csv_data,
                file_name="high_risk_customers.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No customers found with a churn probability >= {high_risk_threshold}%.")
    else:
        st.warning("⚠️ Insufficient data or missing required columns to train the Churn Model.")
