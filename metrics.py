import streamlit as st
import pandas as pd
from transform import calculate_aov, calculate_delta

def get_yoy_caption(curr_val, prev_val, has_prev):
    if not has_prev or prev_val == 0 or pd.isna(prev_val) or pd.isna(curr_val):
        return "YoY: N/A"
    pct = ((curr_val - prev_val) / prev_val) * 100
    if pct > 0:
        return f"📈 YoY: +{pct:.1f}%"
    elif pct < 0:
        return f"📉 YoY: {pct:.1f}%"
    else:
        return "➖ YoY: 0.0%"

def render_metrics(df: pd.DataFrame):
    """
    Computes and displays top-level KPIs adaptively based on available canonical columns.
    """
    st.subheader("Top-Level KPIs")
    
    # 1. Base check for MoM and YoY logic
    curr_df = pd.DataFrame()
    prev_month_df = pd.DataFrame()
    curr_year_df = pd.DataFrame()
    prev_year_df = pd.DataFrame()
    
    if "order_date" in df.columns and not df.empty:
        # Date must be parsed
        if pd.api.types.is_datetime64_any_dtype(df["order_date"]):
            max_date = df["order_date"].max()
            
            # Isolate Current Month Data
            curr_mask = (df["order_date"].dt.year == max_date.year) & (df["order_date"].dt.month == max_date.month)
            curr_df = df[curr_mask]
            
            # Isolate Previous Month Data (Handling Jan -> Dec rollover)
            prev_month_year = max_date.year if max_date.month > 1 else max_date.year - 1
            prev_month_val = max_date.month - 1 if max_date.month > 1 else 12
            prev_month_mask = (df["order_date"].dt.year == prev_month_year) & (df["order_date"].dt.month == prev_month_val)
            prev_month_df = df[prev_month_mask]
            
            # Isolate Current Year and Previous Year Data
            curr_year_mask = (df["order_date"].dt.year == max_date.year)
            curr_year_df = df[curr_year_mask]
            
            prev_year_mask = (df["order_date"].dt.year == max_date.year - 1)
            prev_year_df = df[prev_year_mask]
            
    has_prev_month = not prev_month_df.empty
    has_prev_year = not prev_year_df.empty
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Total Sales
    with col1:
        if "sales" in df.columns:
            total_sales = df["sales"].sum()
            sales_delta = None
            if has_prev_month:
                sales_delta = calculate_delta(curr_df["sales"].sum(), prev_month_df["sales"].sum())
            st.metric(label="Total Sales", value=f"${total_sales:,.2f}", delta=f"{sales_delta} MoM" if sales_delta else None)
            
            curr_y_sales = curr_year_df["sales"].sum() if not curr_year_df.empty else 0
            prev_y_sales = prev_year_df["sales"].sum() if not prev_year_df.empty else 0
            st.caption(get_yoy_caption(curr_y_sales, prev_y_sales, has_prev_year))
        else:
            st.metric(label="Total Sales", value="N/A", delta=None)
            st.caption("YoY: N/A")
            
    # 2. Unique Customers
    with col2:
        if "customer_id" in df.columns:
            total_customers = df["customer_id"].nunique()
            cust_delta = None
            if has_prev_month:
                cust_delta = calculate_delta(curr_df["customer_id"].nunique(), prev_month_df["customer_id"].nunique())
            st.metric(label="Unique Customers", value=f"{total_customers:,}", delta=f"{cust_delta} MoM" if cust_delta else None)
            
            curr_y_cust = curr_year_df["customer_id"].nunique() if not curr_year_df.empty else 0
            prev_y_cust = prev_year_df["customer_id"].nunique() if not prev_year_df.empty else 0
            st.caption(get_yoy_caption(curr_y_cust, prev_y_cust, has_prev_year))
        else:
            st.metric(label="Unique Customers", value="N/A", delta=None)
            st.caption("YoY: N/A")
            
    # 3. Total Orders
    with col3:
        if "order_id" in df.columns:
            total_orders = df["order_id"].nunique()
            orders_delta = None
            if has_prev_month:
                orders_delta = calculate_delta(curr_df["order_id"].nunique(), prev_month_df["order_id"].nunique())
            st.metric(label="Total Orders", value=f"{total_orders:,}", delta=f"{orders_delta} MoM" if orders_delta else None)
            
            curr_y_ord = curr_year_df["order_id"].nunique() if not curr_year_df.empty else 0
            prev_y_ord = prev_year_df["order_id"].nunique() if not prev_year_df.empty else 0
            st.caption(get_yoy_caption(curr_y_ord, prev_y_ord, has_prev_year))
        else:
            # Fallback to row count if order_id isn't present
            total_orders = len(df)
            orders_delta = None
            if has_prev_month:
                orders_delta = calculate_delta(len(curr_df), len(prev_month_df))
            st.metric(label="Total Rows (Orders)", value=f"{total_orders:,}", delta=f"{orders_delta} MoM" if orders_delta else None)
            
            curr_y_rows = len(curr_year_df) if not curr_year_df.empty else 0
            prev_y_rows = len(prev_year_df) if not prev_year_df.empty else 0
            st.caption(get_yoy_caption(curr_y_rows, prev_y_rows, has_prev_year))
            
    # 4. Average Order Value
    with col4:
        if "sales" in df.columns:
            if "order_id" in df.columns:
                aov = calculate_aov(df["sales"].sum(), df["order_id"].nunique())
                aov_delta = None
                if has_prev_month:
                    curr_orders = curr_df["order_id"].nunique()
                    prev_orders = prev_month_df["order_id"].nunique()
                    curr_aov = calculate_aov(curr_df["sales"].sum(), curr_orders)
                    prev_aov = calculate_aov(prev_month_df["sales"].sum(), prev_orders)
                    aov_delta = calculate_delta(curr_aov, prev_aov)
                st.metric(label="Average Order Value", value=f"${aov:,.2f}", delta=f"{aov_delta} MoM" if aov_delta else None)
                
                curr_y_aov = calculate_aov(curr_year_df["sales"].sum(), curr_year_df["order_id"].nunique()) if not curr_year_df.empty else 0
                prev_y_aov = calculate_aov(prev_year_df["sales"].sum(), prev_year_df["order_id"].nunique()) if not prev_year_df.empty else 0
                st.caption(get_yoy_caption(curr_y_aov, prev_y_aov, has_prev_year))
            else:
                # If we don't have order_id, we can't reliably calculate AOV
                st.metric(label="Average Order Value", value="N/A", delta=None)
                st.caption("YoY: N/A")
        else:
            st.metric(label="Average Order Value", value="N/A", delta=None)
            st.caption("YoY: N/A")
