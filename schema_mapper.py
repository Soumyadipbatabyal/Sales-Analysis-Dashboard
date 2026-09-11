import streamlit as st
import pandas as pd
import difflib

# Canonical fields MUST exactly match these strings across the entire application
CANONICAL_FIELDS = [
    "order_date", "sales", "quantity", "profit", "category", 
    "sub_category", "region", "state", "customer_id", "order_id", "segment"
]

ALIAS_MAP = {
    "order_date": ["order date", "date", "purchase date", "orderdt", "order_date", "order-date", "orderdate", "transaction date", "date of purchase"],
    "sales": ["sales", "revenue", "amount", "total sales", "order amount", "gross sales", "price"],
    "quantity": ["quantity", "qty", "units", "amount", "order quantity"],
    "profit": ["profit", "margin", "net profit", "net margin"],
    "category": ["category", "product category", "department", "cat"],
    "sub_category": ["sub_category", "sub category", "sub-category", "sub cat", "sub_cat"],
    "region": ["region", "territory", "area", "zone"],
    "state": ["state", "province", "st"],
    "customer_id": ["customer_id", "customer id", "customer", "buyer id", "client id", "cust id", "cust_id"],
    "order_id": ["order_id", "order id", "invoice no", "invoice id", "order no", "order_no", "order #", "invoice #"],
    "segment": ["segment", "customer segment", "client segment", "market segment"]
}

def is_date_like(series: pd.Series) -> bool:
    """Check if a series can be parsed as a datetime."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    # Try converting a small sample to see if it works
    sample = series.dropna().head(100)
    if len(sample) == 0:
        return False
    try:
        pd.to_datetime(sample, errors='raise')
        return True
    except (ValueError, TypeError):
        return False

def is_numeric_like(series: pd.Series) -> bool:
    """Check if a series can be treated as numeric."""
    if pd.api.types.is_numeric_dtype(series):
        return True
    sample = series.dropna().head(100)
    if len(sample) == 0:
        return False
    # If it's strings, maybe it has $ or commas
    if pd.api.types.is_string_dtype(series):
        sample = sample.astype(str).str.replace(r'[\$,]', '', regex=True)
        try:
            pd.to_numeric(sample, errors='raise')
            return True
        except (ValueError, TypeError):
            return False
    return False

def guess_mapping(df: pd.DataFrame) -> dict:
    """
    Score uploaded columns against canonical fields using fuzzy matching and dtype hints.
    """
    guessed_mapping = {}
    uploaded_columns = list(df.columns)
    
    # Keep track of which uploaded columns have been mapped to avoid mapping one to multiple
    used_columns = set()
    
    for canonical, aliases in ALIAS_MAP.items():
        best_match = None
        best_score = 0.0
        
        for col in uploaded_columns:
            if col in used_columns:
                continue
                
            col_lower = col.lower().strip()
            
            # Direct match
            if col_lower in aliases:
                best_match = col
                best_score = 1.0
                break
                
            # Fuzzy match
            for alias in aliases:
                score = difflib.SequenceMatcher(None, col_lower, alias).ratio()
                if score > best_score:
                    best_score = score
                    best_match = col
                    
        # Apply dtype penalty/boost if we found a decent string match
        if best_match and best_score > 0.6:
            if canonical == "order_date":
                if not is_date_like(df[best_match]):
                    best_score -= 0.5
            elif canonical in ["sales", "quantity", "profit"]:
                if not is_numeric_like(df[best_match]):
                    best_score -= 0.5
                    
        if best_score >= 0.6 and best_match:
            guessed_mapping[canonical] = best_match
            used_columns.add(best_match)
        else:
            guessed_mapping[canonical] = None
            
    return guessed_mapping

def render_mapping_ui(df: pd.DataFrame) -> dict:
    """
    Renders UI for the user to confirm or correct the guessed column mapping.
    Returns the final confirmed mapping, or None if not yet confirmed.
    """
    st.subheader("Data Schema Mapping")
    st.write("We detected the following columns in your CSV. Please map them to the standard fields needed for the dashboard.")
    
    selection_mode = st.radio("Column Selection Mode:", ["Auto (Show all columns)", "Manual (Specify number)"], horizontal=True)
    if selection_mode == "Manual (Specify number)":
        num_cols = st.number_input("How many headers do you want to add?", min_value=1, max_value=len(df.columns), value=min(5, len(df.columns)))
    else:
        num_cols = len(df.columns)
    
    if "best_guess_mapping" not in st.session_state:
        st.session_state.best_guess_mapping = guess_mapping(df)
        
    guessed = st.session_state.best_guess_mapping
    # Create an inverse mapping: {uploaded_col: canonical}
    inverse_guessed = {v: k for k, v in guessed.items() if v is not None}
    
    options = ["Ignore / Do not map"] + CANONICAL_FIELDS
    current_mapping = {}
    
    # We display these in 3 columns for better UI layout
    cols = st.columns(3)
    
    with st.form("mapping_form"):
        for idx, csv_col in enumerate(list(df.columns)[:num_cols], start=1):
            col_idx = (idx - 1) % 3
            with cols[col_idx]:
                st.caption(f"Column: {csv_col}")
                
                guess_canonical = inverse_guessed.get(csv_col)
                default_idx = 0
                if guess_canonical in options:
                    default_idx = options.index(guess_canonical)
                
                # Render selectbox
                selection = st.selectbox(
                    f"Select {idx}",
                    options=options,
                    index=default_idx,
                    key=f"sel_{csv_col}"
                )
                
                if selection != "Ignore / Do not map":
                    current_mapping[selection] = csv_col
                    
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit = st.form_submit_button("Confirm Mapping & Continue", use_container_width=True)
        with col_btn2:
            apply_all = st.form_submit_button("⚡ Apply All & Continue", use_container_width=True)
        
        if apply_all:
            return guessed
        elif submit:
            return current_mapping
            
    return None

def apply_mapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """
    Renames the dataframe columns to the canonical names based on the mapping.
    Only includes columns that were mapped to a canonical field.
    """
    # Reverse mapping: {uploaded_col: canonical_field}
    rename_dict = {v: k for k, v in mapping.items() if v is not None}
    
    # Keep only the mapped columns to avoid clutter and potential naming conflicts
    # However, user might want to see unmapped columns in preview? 
    # For now, let's keep all columns but rename the mapped ones.
    renamed_df = df.rename(columns=rename_dict)
    
    return renamed_df
