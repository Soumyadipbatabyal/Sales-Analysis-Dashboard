import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    
    # --- START OF MoM LOGIC ---
    sales_delta, cust_delta, orders_delta, aov_delta = None, None, None, None

    if "Order Date" in filtered_df.columns and not filtered_df.empty:
        max_date = filtered_df["Order Date"].max()
        
        # Isolate Current Month Data
        curr_mask = (filtered_df["Order Date"].dt.year == max_date.year) & (filtered_df["Order Date"].dt.month == max_date.month)
        curr_df = filtered_df[curr_mask]
        
        # Isolate Previous Month Data (Handling Jan -> Dec rollover)
        prev_year = max_date.year if max_date.month > 1 else max_date.year - 1
        prev_month = max_date.month - 1 if max_date.month > 1 else 12
        prev_mask = (filtered_df["Order Date"].dt.year == prev_year) & (filtered_df["Order Date"].dt.month == prev_month)
        prev_df = filtered_df[prev_mask]
        
        # Safe delta calculator to prevent division by zero
        def calc_delta(curr_val, prev_val):
            if prev_val == 0:
                return None
            return f"{((curr_val - prev_val) / prev_val) * 100:.1f}%"

        # Calculate metrics ONLY if we have a valid previous period to compare against
        if not prev_df.empty:
            if "Sales" in filtered_df.columns:
                sales_delta = calc_delta(curr_df["Sales"].sum(), prev_df["Sales"].sum())
            if "Customer ID" in filtered_df.columns:
                cust_delta = calc_delta(curr_df["Customer ID"].nunique(), prev_df["Customer ID"].nunique())
            if "Order ID" in filtered_df.columns:
                prev_orders = prev_df["Order ID"].nunique()
                curr_orders = curr_df["Order ID"].nunique()
                orders_delta = calc_delta(curr_orders, prev_orders)
                if "Sales" in filtered_df.columns and prev_orders > 0 and curr_orders > 0:
                    aov_delta = calc_delta(curr_df["Sales"].sum() / curr_orders, prev_df["Sales"].sum() / prev_orders)
            else:
                orders_delta = calc_delta(len(curr_df), len(prev_df))
    # --- END OF MoM LOGIC ---

    col1, col2, col3, col4 = st.columns(4)
    
    if "Order ID" in filtered_df.columns:
        total_orders = filtered_df["Order ID"].nunique()
    else:
        total_orders = len(filtered_df)

    with col1:
        if "Sales" in filtered_df.columns:
            total_sales = filtered_df["Sales"].sum()
            st.metric(label="Total Sales", value=f"${total_sales:,.2f}", delta=sales_delta)
        else:
            st.warning("⚠️ 'Sales' column missing.")
            
    with col2:
        if "Customer ID" in filtered_df.columns:
            total_customers = filtered_df["Customer ID"].nunique()
            st.metric(label="Unique Customers", value=f"{total_customers:,}", delta=cust_delta)
        else:
            st.warning("⚠️ 'Customer ID' missing.")
            
    with col3:
        st.metric(label="Total Orders", value=f"{total_orders:,}", delta=orders_delta)

    with col4:
        if "Sales" in filtered_df.columns and total_orders > 0:
            aov = filtered_df["Sales"].sum() / total_orders
            st.metric(label="Average Order Value", value=f"${aov:,.2f}", delta=aov_delta)
        else:
            st.warning("⚠️ Cannot calculate AOV.")

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
                st.plotly_chart(fig_trend, key="trend_chart_tab", width="stretch")
            else:
                st.warning("⚠️ Cannot render chart: missing 'Order Date' and/or 'Sales' columns.")

        with chart_col2:
            st.subheader("Sales by Sub-Category")
            if 'Sub-Category' in filtered_df.columns and 'Sales' in filtered_df.columns:
                subcategory_sales = filtered_df.groupby("Sub-Category")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=True)
                fig_subcat = px.bar(subcategory_sales, x='Sales', y='Sub-Category', orientation='h')
                st.plotly_chart(fig_subcat, key="subcat_chart_tab", width="stretch")
            else:
                st.warning("⚠️ Cannot render chart: missing 'Sub-Category' and/or 'Sales' columns.")

        # --- NEW PARETO CHART ---
        st.divider()
        st.subheader("Pareto Analysis: Sales by Sub-Category")
        st.markdown("Visualizing which products drive 80% of total revenue.")
        
        if 'Sub-Category' in filtered_df.columns and 'Sales' in filtered_df.columns:
            # Calculate descending sales and cumulative percentage
            pareto_df = filtered_df.groupby("Sub-Category")["Sales"].sum().reset_index().sort_values(by="Sales", ascending=False)
            pareto_df["Cumulative %"] = (pareto_df["Sales"].cumsum() / pareto_df["Sales"].sum()) * 100
            
            # Build the dual-axis chart
            fig_pareto = go.Figure()
            
            # Bar chart for raw sales
            fig_pareto.add_trace(go.Bar(
                x=pareto_df['Sub-Category'],
                y=pareto_df['Sales'],
                name='Sales',
                marker_color='#3366CC'
            ))
            
            # Line chart for cumulative percentage
            fig_pareto.add_trace(go.Scatter(
                x=pareto_df['Sub-Category'],
                y=pareto_df['Cumulative %'],
                name='Cumulative %',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color='#FF9900', width=3)
            ))
            
            # Format the dual-axis layout
            fig_pareto.update_layout(
                yaxis=dict(title='Sales ($)'),
                yaxis2=dict(
                    title='Cumulative %',
                    overlaying='y',
                    side='right',
                    range=[0, 110]
                ),
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            # Add a dotted line marking the 80% threshold
            fig_pareto.add_hline(y=80, yref="y2", line_dash="dot", annotation_text="80% Threshold", annotation_position="bottom right")
            
            st.plotly_chart(fig_pareto, key="pareto_chart", width="stretch")
        else:
            st.warning("⚠️ Cannot render Pareto chart: missing 'Sub-Category' and/or 'Sales' columns.")
        # --- END PARETO CHART ---

    with tab2:
        adv_col1, adv_col2 = st.columns(2)

        with adv_col1:
            st.subheader("Sales by Customer Segment")
            if 'Segment' in filtered_df.columns and 'Sales' in filtered_df.columns:
                segment_sales = filtered_df.groupby("Segment")["Sales"].sum().reset_index()
                fig_segment = px.pie(segment_sales, values='Sales', names='Segment', hole=0.4)
                st.plotly_chart(fig_segment, key="segment_chart_tab", width="stretch")
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
                st.plotly_chart(fig_map, key="map_chart_tab", width="stretch")
            else:
                st.warning("⚠️ Cannot render chart: missing 'State' and/or 'Sales' columns.")

    with tab3:
        # 6. Raw Data & Export
        st.subheader("Raw Data View (First 100 Rows)")
        st.dataframe(filtered_df.head(100), width="stretch")

        st.divider()
        st.subheader("Export Your Data")
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download Filtered Data as CSV", data=csv_data, file_name="filtered_superstore_data.csv", mime="text/csv")