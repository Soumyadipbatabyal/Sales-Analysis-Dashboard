import pandas as pd

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies feature engineering to the cleaned dataframe.
    Derives date parts and other necessary columns.
    """
    transformed_df = df.copy()
    
    if "order_date" in transformed_df.columns:
        # Ensure it's datetime just in case
        if pd.api.types.is_datetime64_any_dtype(transformed_df["order_date"]):
            transformed_df["order_year"] = transformed_df["order_date"].dt.year
            transformed_df["order_month"] = transformed_df["order_date"].dt.month
            transformed_df["order_quarter"] = transformed_df["order_date"].dt.quarter
            transformed_df["order_weekday"] = transformed_df["order_date"].dt.day_name()
            transformed_df["order_year_month"] = transformed_df["order_date"].dt.to_period('M')
            
    return transformed_df

def calculate_aov(sales_sum: float, unique_orders: int) -> float:
    """
    Calculates Average Order Value safely.
    """
    if unique_orders == 0 or pd.isna(unique_orders):
        return 0.0
    return float(sales_sum) / unique_orders

def calculate_delta(curr_val: float, prev_val: float) -> str:
    """
    Safe delta calculator to prevent division by zero.
    Returns formatted percentage string or None.
    """
    if prev_val == 0 or pd.isna(prev_val) or pd.isna(curr_val):
        return None
    return f"{((curr_val - prev_val) / prev_val) * 100:.1f}%"
