import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

def train_churn_model(df: pd.DataFrame):
    """
    Trains a Random Forest classifier to predict customer churn based on RFM features.
    Returns:
        results_df (pd.DataFrame): Customers with predictions and risk categories.
        feature_importances (pd.DataFrame): Importance of each RFM feature.
    """
    required_cols = ['customer_id', 'order_date', 'sales']
    for col in required_cols:
        if col not in df.columns:
            return None, None
            
    # Ensure order_date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['order_date']):
        return None, None

    # Calculate RFM metrics per customer
    max_date = df['order_date'].max()
    
    # Recency: days since last purchase
    # Frequency: number of unique orders (if order_id exists, else row count)
    # Monetary: total sales
    
    agg_funcs = {
        'order_date': lambda x: (max_date - x.max()).days,
        'sales': 'sum'
    }
    
    if 'order_id' in df.columns:
        agg_funcs['order_id'] = 'nunique'
    else:
        agg_funcs['order_date'] = 'count' # fallback for frequency if no order_id
        
    rfm = df.groupby('customer_id').agg(agg_funcs).reset_index()
    
    if 'order_id' in df.columns:
        rfm.rename(columns={'order_date': 'Recency', 'order_id': 'Frequency', 'sales': 'Monetary'}, inplace=True)
    else:
        # If we used order_date twice, the pandas aggregation might have renamed things awkwardly, 
        # let's be explicit by using named aggregation to avoid issues.
        rfm = df.groupby('customer_id').agg(
            Recency=('order_date', lambda x: (max_date - x.max()).days),
            Frequency=('customer_id', 'count'),
            Monetary=('sales', 'sum')
        ).reset_index()
    
    # Calculate AOV
    rfm['AOV'] = rfm['Monetary'] / rfm['Frequency']
    
    # Fill any potential NaNs
    rfm = rfm.fillna(0)
    
    if len(rfm) < 10:
        return None, None # Not enough data to train a model
        
    # Define Churn target: Recency > 75th percentile
    recency_75th = rfm['Recency'].quantile(0.75)
    rfm['Churn_Target'] = (rfm['Recency'] > recency_75th).astype(int)
    
    # Features and Target
    X = rfm[['Recency', 'Frequency', 'Monetary', 'AOV']]
    y = rfm['Churn_Target']
    
    # Train model
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    
    # Predict probabilities
    churn_probs = clf.predict_proba(X)[:, 1]
    rfm['Churn Probability'] = churn_probs * 100
    
    # Risk Categories
    conditions = [
        (rfm['Churn Probability'] >= 70),
        (rfm['Churn Probability'] >= 40)
    ]
    choices = ['High', 'Medium']
    rfm['Risk Category'] = np.select(conditions, choices, default='Low')
    
    # Feature Importances
    importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': clf.feature_importances_
    }).sort_values(by='Importance', ascending=True)
    
    return rfm, importances

def forecast_sales(df: pd.DataFrame, forecast_days: int = 30):
    """
    Trains a Random Forest Regressor to forecast daily sales.
    Returns:
        forecast_df (pd.DataFrame): Historical and forecasted sales with confidence intervals.
    """
    required_cols = ['order_date', 'sales']
    for col in required_cols:
        if col not in df.columns:
            return None
            
    if not pd.api.types.is_datetime64_any_dtype(df['order_date']):
        return None
        
    # Aggregate sales by day
    daily_sales = df.groupby(df['order_date'].dt.floor('D'))['sales'].sum().reset_index()
    
    # Fill missing dates with 0
    if daily_sales.empty:
        return None
        
    min_date = daily_sales['order_date'].min()
    max_date = daily_sales['order_date'].max()
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    daily_sales = daily_sales.set_index('order_date').reindex(full_date_range, fill_value=0).reset_index()
    daily_sales.rename(columns={'index': 'order_date'}, inplace=True)
    
    if len(daily_sales) < 14:
        return None # Not enough history to train a meaningful model
        
    # Feature Engineering
    def engineer_features(data):
        d = data.copy()
        d['day_of_week'] = d['order_date'].dt.dayofweek
        d['day_of_month'] = d['order_date'].dt.day
        d['day_of_year'] = d['order_date'].dt.dayofyear
        # Linear trend index
        d['trend_index'] = (d['order_date'] - d['order_date'].min()).dt.days
        return d
        
    featured_data = engineer_features(daily_sales)
    
    X = featured_data[['day_of_week', 'day_of_month', 'day_of_year', 'trend_index']]
    y = featured_data['sales']
    
    # Train model
    reg = RandomForestRegressor(n_estimators=100, random_state=42)
    reg.fit(X, y)
    
    # Create future dataframe
    future_dates = pd.date_range(start=max_date + pd.Timedelta(days=1), periods=forecast_days, freq='D')
    future_df = pd.DataFrame({'order_date': future_dates})
    
    # We need 'trend_index' relative to the original minimum date
    future_featured = future_df.copy()
    future_featured['day_of_week'] = future_featured['order_date'].dt.dayofweek
    future_featured['day_of_month'] = future_featured['order_date'].dt.day
    future_featured['day_of_year'] = future_featured['order_date'].dt.dayofyear
    future_featured['trend_index'] = (future_featured['order_date'] - min_date).dt.days
    
    X_future = future_featured[['day_of_week', 'day_of_month', 'day_of_year', 'trend_index']]
    
    # Predict
    future_predictions = reg.predict(X_future)
    future_df['sales'] = future_predictions
    future_df['Type'] = 'Predicted'
    
    # Prepare historical data
    hist_df = daily_sales.copy()
    hist_df['Type'] = 'Actual'
    
    # Combine
    combined_df = pd.concat([hist_df, future_df], ignore_index=True)
    
    # Confidence intervals (Estimated +/- 10% for predicted)
    combined_df['Lower_CI'] = combined_df.apply(lambda row: row['sales'] * 0.9 if row['Type'] == 'Predicted' else None, axis=1)
    combined_df['Upper_CI'] = combined_df.apply(lambda row: row['sales'] * 1.1 if row['Type'] == 'Predicted' else None, axis=1)
    
    return combined_df
