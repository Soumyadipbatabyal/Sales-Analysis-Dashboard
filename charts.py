import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def render_monthly_sales_trend(df: pd.DataFrame):
    """Monthly Sales Trend Line Chart."""
    st.subheader("Monthly Sales Trend")
    if "order_date" in df.columns and "sales" in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df["order_date"]):
            monthly_sales = df.groupby(df['order_date'].dt.to_period('M'))['sales'].sum().reset_index()
            monthly_sales['order_date'] = monthly_sales['order_date'].dt.to_timestamp()
            fig = px.line(monthly_sales, x='order_date', y='sales')
            st.plotly_chart(fig, key="trend_chart_tab", width="stretch")
        else:
            st.warning("⚠️ 'order_date' could not be parsed as dates.")
    else:
        st.warning("⚠️ Cannot render chart: missing 'order_date' and/or 'sales' columns.")

def render_sales_by_subcategory(df: pd.DataFrame):
    """Sales by Sub-Category Bar Chart."""
    st.subheader("Sales by Sub-Category")
    if "sub_category" in df.columns and "sales" in df.columns:
        subcategory_sales = df.groupby("sub_category")["sales"].sum().reset_index().sort_values(by="sales", ascending=True)
        fig = px.bar(subcategory_sales, x='sales', y='sub_category', orientation='h')
        st.plotly_chart(fig, key="subcat_chart_tab", width="stretch")
    else:
        st.warning("⚠️ Cannot render chart: missing 'sub_category' and/or 'sales' columns.")

def render_pareto_chart(df: pd.DataFrame):
    """Pareto Analysis: Sales by Sub-Category."""
    st.subheader("Pareto Analysis: Sales by Sub-Category")
    st.markdown("Visualizing which products drive 80% of total revenue.")
    
    if "sub_category" in df.columns and "sales" in df.columns:
        pareto_df = df.groupby("sub_category")["sales"].sum().reset_index().sort_values(by="sales", ascending=False)
        if pareto_df["sales"].sum() > 0:
            pareto_df["Cumulative %"] = (pareto_df["sales"].cumsum() / pareto_df["sales"].sum()) * 100
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=pareto_df['sub_category'],
                y=pareto_df['sales'],
                name='Sales',
                marker_color='#3366CC'
            ))
            
            fig.add_trace(go.Scatter(
                x=pareto_df['sub_category'],
                y=pareto_df['Cumulative %'],
                name='Cumulative %',
                mode='lines+markers',
                yaxis='y2',
                line=dict(color='#FF9900', width=3)
            ))
            
            fig.update_layout(
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
            
            fig.add_hline(y=80, yref="y2", line_dash="dot", annotation_text="80% Threshold", annotation_position="bottom right")
            st.plotly_chart(fig, key="pareto_chart", width="stretch")
        else:
             st.warning("⚠️ Cannot render chart: Total sales is 0.")
    else:
        st.warning("⚠️ Cannot render Pareto chart: missing 'sub_category' and/or 'sales' columns.")

def render_sales_by_segment(df: pd.DataFrame):
    """Sales by Customer Segment Donut Chart."""
    st.subheader("Sales by Customer Segment")
    if "segment" in df.columns and "sales" in df.columns:
        segment_sales = df.groupby("segment")["sales"].sum().reset_index()
        fig = px.pie(segment_sales, values='sales', names='segment', hole=0.4)
        st.plotly_chart(fig, key="segment_chart_tab", width="stretch")
    else:
        st.warning("⚠️ Cannot render chart: missing 'segment' and/or 'sales' columns.")

def render_sales_map(df: pd.DataFrame):
    """Geographical Sales Map by State."""
    st.subheader("Geographical Sales Map")
    if "state" in df.columns and "sales" in df.columns:
        us_state_abbrev = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
            'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
            'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
            'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
            'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
            'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
            'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
            'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
            'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
            'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
            'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
            'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
            'Wisconsin': 'WI', 'Wyoming': 'WY', 'District of Columbia': 'DC'
        }
        state_map_data = df.groupby("state")["sales"].sum().reset_index()
        # Normalization handled in cleaning.py (strip + title case), so it should match the keys here
        state_map_data['state_code'] = state_map_data['state'].map(us_state_abbrev).fillna(state_map_data['state'])
        
        fig = px.scatter_geo(
            state_map_data, 
            locations="state_code", 
            locationmode="USA-states",
            color="sales",
            size="sales",
            scope="usa"
        )
        st.plotly_chart(fig, key="map_chart_tab", width="stretch")
    else:
        st.warning("⚠️ Cannot render chart: missing 'state' and/or 'sales' columns.")

def plot_churn_risk(churn_df: pd.DataFrame, importances_df: pd.DataFrame):
    """
    Renders churn risk charts (Donut chart for risk levels, horizontal bar for feature importance).
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Risk Distribution")
        if 'Risk Category' in churn_df.columns:
            risk_counts = churn_df['Risk Category'].value_counts().reset_index()
            risk_counts.columns = ['Risk Category', 'Count']
            
            # Map colors for consistency
            color_map = {'High': '#FF4B4B', 'Medium': '#FFA500', 'Low': '#00CC96'}
            
            fig = px.pie(
                risk_counts, 
                values='Count', 
                names='Risk Category', 
                hole=0.4,
                color='Risk Category',
                color_discrete_map=color_map
            )
            st.plotly_chart(fig, key="churn_risk_donut", width="stretch")
        else:
            st.warning("⚠️ Risk Category data missing.")
            
    with col2:
        st.subheader("Key Drivers of Churn")
        if importances_df is not None and not importances_df.empty:
            fig = px.bar(
                importances_df,
                x='Importance',
                y='Feature',
                orientation='h',
                color='Importance',
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, key="churn_importance_bar", width="stretch")
        else:
            st.warning("⚠️ Feature importances not available.")

def plot_sales_forecast(forecast_df: pd.DataFrame):
    """
    Renders a line chart for historical and forecasted sales with confidence intervals.
    """
    st.subheader("Sales Forecast")
    
    if forecast_df is not None and not forecast_df.empty:
        fig = go.Figure()

        # Split data
        actual_df = forecast_df[forecast_df['Type'] == 'Actual']
        pred_df = forecast_df[forecast_df['Type'] == 'Predicted']

        # Add actual sales
        fig.add_trace(go.Scatter(
            x=actual_df['order_date'],
            y=actual_df['sales'],
            name='Historical Sales',
            mode='lines',
            line=dict(color='#1f77b4')
        ))

        if not pred_df.empty:
            # Add predicted sales
            fig.add_trace(go.Scatter(
                x=pred_df['order_date'],
                y=pred_df['sales'],
                name='Forecasted Sales',
                mode='lines',
                line=dict(color='#ff7f0e', dash='dash')
            ))

            # Add confidence interval (shaded area)
            fig.add_trace(go.Scatter(
                x=pd.concat([pred_df['order_date'], pred_df['order_date'][::-1]]),
                y=pd.concat([pred_df['Upper_CI'], pred_df['Lower_CI'][::-1]]),
                fill='toself',
                fillcolor='rgba(255,127,14,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='Confidence Interval (±10%)'
            ))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Sales ($)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, key="sales_forecast_chart", width="stretch")
    else:
        st.warning("⚠️ Forecast data not available.")
