import streamlit as st
import pandas as pd

def render_report_tab(df: pd.DataFrame):
    """
    Renders the data preview and export tab.
    """
    st.subheader("Filtered Data Summary")
    
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns([1, 2, 1, 1])
    
    total_filtered_rows = len(df)
    stats_col1.metric("Total Rows", f"{total_filtered_rows:,}")
    
    if "order_date" in df.columns and not df.empty and pd.api.types.is_datetime64_any_dtype(df["order_date"]):
        min_date = df['order_date'].min().strftime('%m/%d/%y')
        max_date = df['order_date'].max().strftime('%m/%d/%y')
        date_range = f"{min_date} - {max_date}"
    else:
        date_range = "N/A"
    stats_col2.metric("Date Range", date_range)
    
    unique_orders = df['order_id'].nunique() if 'order_id' in df.columns else 0
    stats_col3.metric("Unique Orders", f"{unique_orders:,}")
    
    unique_cust = df['customer_id'].nunique() if 'customer_id' in df.columns else 0
    stats_col4.metric("Unique Customers", f"{unique_cust:,}")

    st.divider()

    st.subheader("Data Preview")
    
    ctrl_col1, ctrl_col2 = st.columns([1, 3])
    with ctrl_col1:
        default_limit = min(100, total_filtered_rows) if total_filtered_rows > 0 else 1
        row_limit = st.number_input("Number of rows to preview", min_value=1, max_value=1000, value=default_limit, step=50)
    with ctrl_col2:
        available_cols = df.columns.tolist()
        selected_cols = st.multiselect("Select columns to display", available_cols, default=available_cols)
        
    if not selected_cols:
        st.warning("⚠️ Please select at least one column to preview.")
    elif df.empty:
        st.warning("⚠️ No data to preview.")
    else:
        preview_df = df[selected_cols].head(row_limit)
        st.markdown(f"**Showing {len(preview_df)} of {total_filtered_rows:,} rows**")
        st.dataframe(preview_df, width="stretch")

    st.divider()
    st.subheader("Export Your Data")
    
    if df.empty:
         st.warning("⚠️ No data to export.")
    else:
        export_df = df[selected_cols] if selected_cols else df
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label=f"📥 Download {total_filtered_rows:,} Filtered Rows as CSV", 
            data=csv_data, 
            file_name="filtered_dashboard_data.csv", 
            mime="text/csv"
        )
