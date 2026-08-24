import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(page_title="Superstore Sales Dashboard", layout="wide")

st.title("📊 Real Data: Superstore Sales Dashboard")
st.markdown("This dashboard is reading directly from your downloaded Kaggle CSV file!")

# 2. Load the Real Data
@st.cache_data
def load_data():
    try:
        data_file = os.environ.get("DATA_FILE", "superstore.csv")
        df = pd.read_csv(data_file, encoding="latin1")
        df.columns = df.columns.str.strip()
        if 'Order Date' in df.columns:
            df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)
        return df
    except FileNotFoundError:
        st.error(f"⚠️ File not found! Please make sure your data file '{data_file}' exists.")
        return None

df = load_data()

# Only run the dashboard if the data loaded successfully
if df is not None:
    # 3. Create the Sidebar Filters
    st.sidebar.header("Dashboard Filters")

    if "Region" in df.columns:
        available_regions = df["Region"].unique()
        selected_regions = st.sidebar.multiselect("Select Region(s)", available_regions, available_regions)
    else:
        selected_regions = []

    if "Category" in df.columns:
        available_categories = df["Category"].unique()
        selected_categories = st.sidebar.multiselect("Select Category", available_categories, available_categories)
    else:
        selected_categories = []

    filtered_df = df.copy()
    if "Region" in df.columns and selected_regions:
        filtered_df = filtered_df[filtered_df["Region"].isin(selected_regions)]
    if "Category" in df.columns and selected_categories:
        filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]

    # Safety check: Stop the app if filters are empty to prevent errors
    if filtered_df.empty:
        st.warning("⚠️ Please select at least one Region and Category from the sidebar to view the dashboard.")
        st.stop()

    # 4. Build the Top-Level KPIs
    col1, col2, col3, col4 = st.columns(4)
    if "Order ID" in filtered_df.columns:
        total_orders = filtered_df["Order ID"].nunique()
    else:
        total_orders = len(filtered_df)

    with col1:
        if "Sales" in filtered_df.columns:
            total_sales = filtered_df["Sales"].sum()
            st.metric(label="Total Sales", value=f"${total_sales:,.2f}")
        else:
            st.warning("⚠️ 'Sales' column missing.")
            
    with col2:
        if "Customer ID" in filtered_df.columns:
            total_customers = filtered_df["Customer ID"].nunique()
            st.metric(label="Unique Customers", value=f"{total_customers:,}")
        else:
            st.warning("⚠️ 'Customer ID' missing.")
            
    with col3:
        st.metric(label="Total Orders", value=f"{total_orders:,}")

    with col4:
        if "Sales" in filtered_df.columns and total_orders > 0:
            aov = filtered_df["Sales"].sum() / total_orders
            st.metric(label="Average Order Value", value=f"${aov:,.2f}")
        else:
            st.warning("⚠️ Cannot calculate AOV.")

    st.divider()

    # 5. Build the Visualizations (100% Plotly)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Monthly Sales Trend")
        if 'Order Date' in filtered_df.columns and 'Sales' in filtered_df.columns:
            monthly_sales = filtered_df.groupby(filtered_df['Order Date'].dt.to_period('M'))['Sales'].sum().reset_index()
            monthly_sales['Order Date'] = monthly_sales['Order Date'].dt.to_timestamp()
            fig_trend = px.line(monthly_sales, x='Order Date', y='Sales')
            st.plotly_chart(fig_trend, key="trend_chart")
        else:
            st.warning("⚠️ Cannot render chart: missing 'Order Date' and/or 'Sales' columns.")

    with chart_col2:
        st.subheader("Sales by Sub-Category")
        if 'Sub-Category' in filtered_df.columns and 'Sales' in filtered_df.columns:
            # We sort ascending here so the biggest bar appears at the TOP of the horizontal chart
            subcategory_sales = filtered_df.groupby("Sub-Category")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=True)
            # Swap x and y, and add orientation='h'
            fig_subcat = px.bar(subcategory_sales, x='Sales', y='Sub-Category', orientation='h')
            st.plotly_chart(fig_subcat, key="subcat_chart")
        else:
            st.warning("⚠️ Cannot render chart: missing 'Sub-Category' and/or 'Sales' columns.")

    st.divider()

    # 5. Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Sales & Trends", "🌍 Geography & Customers", "📥 Data & Export"])

    with tab1:
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Monthly Sales Trend")
            if 'Order Date' in filtered_df.columns and 'Sales' in filtered_df.columns:
                monthly_sales = filtered_df.groupby(filtered_df['Order Date'].dt.to_period('M'))['Sales'].sum().reset_index()
                monthly_sales['Order Date'] = monthly_sales['Order Date'].dt.to_timestamp()
                fig_trend = px.line(monthly_sales, x='Order Date', y='Sales')
                st.plotly_chart(fig_trend, key="trend_chart", use_container_width=True)
            else:
                st.warning("⚠️ Cannot render chart: missing 'Order Date' and/or 'Sales' columns.")

        with chart_col2:
            st.subheader("Sales by Sub-Category")
            if 'Sub-Category' in filtered_df.columns and 'Sales' in filtered_df.columns:
                subcategory_sales = filtered_df.groupby("Sub-Category")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=True)
                fig_subcat = px.bar(subcategory_sales, x='Sales', y='Sub-Category', orientation='h')
                st.plotly_chart(fig_subcat, key="subcat_chart", use_container_width=True)
            else:
                st.warning("⚠️ Cannot render chart: missing 'Sub-Category' and/or 'Sales' columns.")

    with tab2:
        adv_col1, adv_col2 = st.columns(2)

        with adv_col1:
            st.subheader("Sales by Customer Segment")
            if 'Segment' in filtered_df.columns and 'Sales' in filtered_df.columns:
                segment_sales = filtered_df.groupby("Segment")["Sales"].sum().reset_index()
                fig_segment = px.pie(segment_sales, values='Sales', names='Segment', hole=0.4)
                st.plotly_chart(fig_segment, key="segment_chart", use_container_width=True)
            else:
                st.warning("⚠️ Cannot render chart: missing 'Segment' and/or 'Sales' columns.")

        with adv_col2:
            st.subheader("Geographical Sales Map")
            if 'State' in filtered_df.columns and 'Sales' in filtered_df.columns:
                state_map_data = filtered_df.groupby("State")["Sales"].sum().reset_index()
                fig_map = px.scatter_geo(
                    state_map_data, 
                    locations="State", 
                    locationmode="USA-states",
                    color="Sales",
                    size="Sales",
                    scope="usa"
                )
                st.plotly_chart(fig_map, key="map_chart", use_container_width=True)
            else:
                st.warning("⚠️ Cannot render chart: missing 'State' and/or 'Sales' columns.")

    with tab3:
        # 6. Raw Data & Export
        st.subheader("Raw Data View (First 100 Rows)")
        st.dataframe(filtered_df.head(100), use_container_width=True)

        st.divider()
        st.subheader("Export Your Data")
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Filtered Data as CSV", data=csv_data, file_name="filtered_superstore_data.csv", mime="text/csv")