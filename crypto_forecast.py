import yfinance as yf
from prophet import Prophet
import plotly.graph_objects as go
import pandas as pd
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_crypto_data(symbol: str = "BTC-USD", period: str = "1y", interval: str = "1d"):
    """
    Retrieves cryptocurrency data using yfinance with exponential backoff for retries.
    Args:
        symbol (str): The ticker symbol for the cryptocurrency.
        period (str): The time period for the data (e.g., "1y").
        interval (str): The data interval (e.g., "1d").
    Returns:
        pd.DataFrame: A DataFrame with the cryptocurrency data or None if retrieval fails.
    """
    logging.info(f"Fetching data for symbol: {symbol}")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            # Attempt to download data
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if data.empty:
                logging.error(f"No data found for the specified symbol: {symbol}")
                return None

            return data
        except Exception as e:
            retries += 1
            logging.warning(f"Failed to get ticker '{symbol}' reason: {e}")
            logging.info(f"Retrying in {2 ** retries} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(2 ** retries)  # Exponential backoff
    
    logging.error(f"Failed to download data for {symbol} after {max_retries} attempts.")
    return None

def generate_forecast_plot(data: pd.DataFrame, symbol: str = "BTC-USD"):
    """
    Generates a Plotly figure with historical data and a future forecast.

    Args:
        data (pd.DataFrame): The historical cryptocurrency data.
        symbol (str): The cryptocurrency symbol.

    Returns:
        plotly.graph_objects.Figure: The Plotly figure with the plot.
    """
    if 'Close' not in data.columns:
        logging.error("Input data does not contain a 'Close' column.")
        # Create a simple figure indicating the error
        fig = go.Figure()
        fig.add_annotation(
            text="Invalid data format. Missing 'Close' column.",
            xref="paper", yref="paper", showarrow=False
        )
        return fig

    # Prepare data for Prophet
    df = data.reset_index()[['Date', 'Close']]
    df.columns = ['ds', 'y']

    # Initialize and fit Prophet model
    model = Prophet()
    model.fit(df)

    # Make future predictions
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # Create Plotly figure
    fig = go.Figure()

    # Add historical data
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines',
        name='Historical Price',
        line=dict(color='royalblue')
    ))

    # Add forecast data
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        mode='lines',
        name='Forecasted Price',
        line=dict(color='firebrick', dash='dash')
    ))

    # Add uncertainty interval
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        mode='lines',
        name='Lower Bound',
        line=dict(width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        mode='lines',
        name='Upper Bound',
        fill='tonexty',
        fillcolor='rgba(255, 0, 0, 0.1)',
        line=dict(width=0),
        showlegend=False
    ))

    # Update layout for aesthetics
    fig.update_layout(
        title=f'Cryptocurrency Price Forecast for {symbol}',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", color="black"),
        hovermode="x unified",
        margin=dict(l=50, r=50, t=70, b=50),
        xaxis_rangeslider_visible=True,
    )

    return fig
