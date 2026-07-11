import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Superstore Sales Dashboard", layout="wide")

st.title("📊 Real Data: Superstore Sales Dashboard")
st.markdown("This dashboard is now reading directly from your downloaded Kaggle CSV file!")

# 2. Load the Real Data
@st.cache_data
def load_data():
    try:
        # Read the CSV. We use 'latin1' encoding because Kaggle Superstore datasets often require it.
        df = pd.read_csv("superstore.csv", encoding="latin1")
        
        # Clean up column names by stripping any accidental whitespace
        df.columns = df.columns.str.strip()
        
        # Convert the 'Order Date' text into actual DateTime objects so we can plot it properly.
        # We use dayfirst=True because this dataset formats dates as DD/MM/YYYY.
        if 'Order Date' in df.columns:
            df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)
            
        return df
    except FileNotFoundError:
        # If the file isn't found, show a friendly warning instead of crashing
        st.error("⚠️ File not found! Please make sure your downloaded CSV is renamed to 'superstore.csv' and is located in your 'sales analysis dashboard' folder.")
        return None

df = load_data()

# Only run the dashboard if the data loaded successfully
if df is not None:
    # 3. Create the Sidebar Filters
    st.sidebar.header("Dashboard Filters")

    # Region Filter (Safety check in case 'Region' column is missing)
    if "Region" in df.columns:
        available_regions = df["Region"].unique()
        selected_regions = st.sidebar.multiselect(
            "Select Region(s)", 
            options=available_regions, 
            default=available_regions
        )
    else:
        selected_regions = []

    # Category Filter
    if "Category" in df.columns:
        available_categories = df["Category"].unique()
        selected_categories = st.sidebar.multiselect(
            "Select Category",
            options=available_categories,
            default=available_categories
        )
    else:
        selected_categories = []

    # Apply both filters to our dataframe if the columns exist
    filtered_df = df.copy()
    if "Region" in df.columns and selected_regions:
        filtered_df = filtered_df[filtered_df["Region"].isin(selected_regions)]
    if "Category" in df.columns and selected_categories:
        filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]

    # 4. Build the Top-Level KPIs
    col1, col2, col3 = st.columns(3)
    
    total_orders = len(filtered_df)

    with col1:
        if "Sales" in filtered_df.columns:
            total_sales = filtered_df["Sales"].sum()
            st.metric(label="Total Sales", value=f"${total_sales:,.2f}")
        else:
            st.metric(label="Total Sales", value="N/A")
            
    with col2:
        # We replaced Profit with 'Unique Customers' since Profit isn't in your dataset
        if "Customer ID" in filtered_df.columns:
            total_customers = filtered_df["Customer ID"].nunique()
            st.metric(label="Unique Customers", value=f"{total_customers:,}")
        else:
            st.metric(label="Unique Customers", value="N/A")
            
    with col3:
        st.metric(label="Total Orders", value=f"{total_orders:,}")

    st.divider()

    # 5. Build the Visualizations
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Monthly Sales Trend")
        if 'Order Date' in filtered_df.columns and 'Sales' in filtered_df.columns:
            # Group sales by month so the line chart isn't too messy with 4 years of daily data
            monthly_sales = filtered_df.groupby(filtered_df['Order Date'].dt.to_period('M'))['Sales'].sum()
            monthly_sales.index = monthly_sales.index.to_timestamp() # Convert back to dates for plotting
            st.line_chart(monthly_sales)
        else:
            st.info("Need 'Order Date' and 'Sales' columns to show trends.")

    with chart_col2:
        st.subheader("Sales by Sub-Category")
        if 'Sub-Category' in filtered_df.columns and 'Sales' in filtered_df.columns:
            # The dataset has a 'Sub-Category' column (like Chairs, Phones, Paper)
            subcategory_sales = filtered_df.groupby("Sub-Category")["Sales"].sum().sort_values(ascending=False)
            st.bar_chart(subcategory_sales)
        else:
            st.info("Need 'Sub-Category' and 'Sales' columns to show this chart.")

    st.divider()
    
    # Add a second row of charts using the new columns we found in your data
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.subheader("Sales by Customer Segment")
        if 'Segment' in filtered_df.columns and 'Sales' in filtered_df.columns:
            segment_sales = filtered_df.groupby("Segment")["Sales"].sum()
            st.bar_chart(segment_sales)
            
    with chart_col4:
        st.subheader("Top 10 States by Sales")
        if 'State' in filtered_df.columns and 'Sales' in filtered_df.columns:
            state_sales = filtered_df.groupby("State")["Sales"].sum().nlargest(10)
            st.bar_chart(state_sales)

    # 6. Display the Raw Data
    st.subheader("Raw Data View (First 100 Rows)")
    # Show only the first 100 rows so it doesn't freeze the browser
    st.dataframe(filtered_df.head(100))