import pandas as pd
import streamlit as st

def clean_data(df: pd.DataFrame, mapping: dict):
    """
    Cleans the dataframe based on the mapped canonical columns.
    Returns:
        cleaned_df (pd.DataFrame): The cleaned dataframe
        quality_report (dict): A dictionary containing data quality metrics
    """
    cleaned_df = df.copy()
    initial_rows = len(cleaned_df)
    
    quality_report = {
        "initial_rows": initial_rows,
        "duplicates_removed": 0,
        "date_parse_failures": 0,
        "numeric_parse_failures": {},
        "missing_values": {}
    }
    
    # 1. Remove Duplicates
    cleaned_df = cleaned_df.drop_duplicates()
    quality_report["duplicates_removed"] = initial_rows - len(cleaned_df)
    
    # Check what canonical columns we actually have in the mapped dataframe
    # The keys of mapping are the canonical fields, and the values are the original columns.
    # But after `apply_mapping`, the dataframe already has the canonical names as columns.
    available_canonical_cols = [k for k, v in mapping.items() if v is not None and k in cleaned_df.columns]
    
    # 2. Date Coercion
    if "order_date" in available_canonical_cols:
        before_nulls = cleaned_df["order_date"].isna().sum()
        cleaned_df["order_date"] = pd.to_datetime(cleaned_df["order_date"], errors="coerce", format='mixed')
        after_nulls = cleaned_df["order_date"].isna().sum()
        quality_report["date_parse_failures"] = after_nulls - before_nulls
        
    # 3. Numeric Coercion
    numeric_cols = ["sales", "quantity", "profit"]
    for col in numeric_cols:
        if col in available_canonical_cols:
            # Remove common currency symbols and commas if it's string type
            if pd.api.types.is_string_dtype(cleaned_df[col]):
                cleaned_df[col] = cleaned_df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
                
            before_nulls = cleaned_df[col].isna().sum()
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")
            after_nulls = cleaned_df[col].isna().sum()
            quality_report["numeric_parse_failures"][col] = after_nulls - before_nulls
            
    # 4. Categorical Normalization
    categorical_cols = ["region", "category", "segment", "sub_category", "state"]
    for col in categorical_cols:
        if col in available_canonical_cols:
            if pd.api.types.is_string_dtype(cleaned_df[col]):
                # Trim whitespace and title case
                cleaned_df[col] = cleaned_df[col].str.strip().str.title()
                
    # 5. Missing Values Summary
    for col in available_canonical_cols:
        missing_count = cleaned_df[col].isna().sum()
        quality_report["missing_values"][col] = {
            "count": missing_count,
            "percentage": (missing_count / len(cleaned_df)) * 100 if len(cleaned_df) > 0 else 0
        }
        
    # Optional: drop rows where critical fields (like order_date or sales) failed to parse?
    # The prompt says "before dropping/flagging them". Let's drop completely unparseable dates 
    # to avoid downstream errors, as a dashboard without a date is hard to trend.
    if "order_date" in available_canonical_cols:
        cleaned_df = cleaned_df.dropna(subset=["order_date"])
        
    quality_report["final_rows"] = len(cleaned_df)
    
    return cleaned_df, quality_report

def render_quality_report(quality_report: dict):
    """
    Renders the Data Quality Report in the Streamlit UI.
    """
    with st.expander("📊 Data Quality Report", expanded=False):
        st.write(f"**Rows Processed:** {quality_report['initial_rows']:,}")
        st.write(f"**Duplicates Removed:** {quality_report['duplicates_removed']:,}")
        
        if quality_report['date_parse_failures'] > 0:
            st.warning(f"**Date Parse Failures:** {quality_report['date_parse_failures']:,} rows had invalid dates and were ignored.")
            
        if quality_report['numeric_parse_failures']:
            for col, failures in quality_report['numeric_parse_failures'].items():
                if failures > 0:
                    st.warning(f"**{col.title()} Parse Failures:** {failures:,} rows had non-numeric values.")
                    
        st.write("**Missing Values Summary:**")
        
        missing_data = []
        for col, stats in quality_report["missing_values"].items():
            missing_data.append({
                "Column": col,
                "Missing Count": stats["count"],
                "Missing %": f"{stats['percentage']:.1f}%"
            })
            
        if missing_data:
            st.dataframe(pd.DataFrame(missing_data), width="stretch")
