import streamlit as st
import pandas as pd
import hashlib
import csv
import io

def calculate_file_hash(file_bytes: bytes) -> str:
    """Calculate MD5 hash of file bytes."""
    return hashlib.md5(file_bytes).hexdigest()

def detect_encoding_and_delimiter(file_bytes: bytes):
    """Attempt to detect encoding and delimiter of a CSV file bytes."""
    encodings = ['utf-8', 'latin1']
    
    for encoding in encodings:
        try:
            text = file_bytes.decode(encoding)
            
            # Grab a sample to sniff delimiter
            sample = text[:4096]
            if not sample:
                continue
                
            try:
                sniffer = csv.Sniffer()
                # Default to comma if sniffer fails or finds nothing common
                dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
                delimiter = dialect.delimiter
            except csv.Error:
                # Fallback to simple comma if sniffer fails
                delimiter = ','
                
            return encoding, delimiter
        except UnicodeDecodeError:
            continue
            
    # Fallback if both fail
    return 'utf-8', ','

@st.cache_data
def load_and_parse_csv(file_bytes: bytes, file_hash: str):
    """
    Load CSV bytes into a DataFrame. 
    Cached based on file_hash to prevent re-reading on every rerun.
    """
    encoding, delimiter = detect_encoding_and_delimiter(file_bytes)
    
    try:
        # We need to wrap the bytes in a string IO for pandas, or just use BytesIO if it accepts encoding
        df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, delimiter=delimiter, low_memory=False)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        return df, None
    except Exception as e:
        return None, str(e)

def handle_file_upload():
    """
    Handles the Streamlit file upload UI and initial parsing.
    Returns:
        file_hash (str): Hash of the uploaded file
        df (pd.DataFrame): The parsed dataframe, or None if error/no file
    """
    
    with st.expander("📊 View Supported Analyses & Data Requirements"):
        st.markdown("""
**Welcome to the Sales Analytics Engine**
Upload your CSV and map your columns to instantly generate insights. 

**Capabilities & Required Data:**
* **Core KPIs:** Requires `Sales`, `Profit`, and `Order ID`
* **Monthly Trends:** Requires `Order Date` and `Sales`
* **Product Performance:** Requires `Category`, `Sub-Category`, and `Sales`
* **Geographical Map:** Requires `State` and `Sales`
* **Customer Demographics:** Requires `Segment` and `Sales`
* **Predictive Insights:** Requires `Order Date`, `Sales`, and `Customer ID`

*(Note: The dashboard gracefully adapts. If your CSV lacks certain columns, those specific charts will safely hide without breaking the app).*
        """)
        
    uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type=["csv"])
    
    if uploaded_file is None:
        return None, None
        
    file_bytes = uploaded_file.getvalue()
    
    if not file_bytes:
        st.error("Uploaded file is empty.")
        return None, None
        
    file_hash = calculate_file_hash(file_bytes)
    
    df, error_msg = load_and_parse_csv(file_bytes, file_hash)
    
    if error_msg:
        st.error(f"Error parsing file: {error_msg}")
        return file_hash, None
        
    if df is None or df.empty or len(df.columns) == 0:
        st.error("The uploaded CSV contains no data or no columns.")
        return file_hash, None
        
    # Validate it's a sales dataset
    sales_keywords = ['sale', 'revenue', 'amount', 'order', 'price', 'profit', 'margin', 'cost', 'qty', 'quantity', 'customer', 'transaction', 'date', 'invoice']
    csv_columns_lower = [col.lower() for col in df.columns]
    
    is_sales_data = any(
        any(keyword in col for keyword in sales_keywords) 
        for col in csv_columns_lower
    )
    
    if not is_sales_data:
        st.error("This CSV does not appear to be a sales dataset. Please upload a valid file.")
        st.stop()
        
    return file_hash, df
