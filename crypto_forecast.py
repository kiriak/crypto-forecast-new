import yfinance as yf
from prophet import Prophet
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot
import logging
from datetime import date, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_prediction_plot(symbol):
    """
    Fetches historical data for a given cryptocurrency symbol,
    trains a Prophet model, makes a 30-day forecast, and
    returns the Plotly plot as an HTML string.

    Args:
        symbol (str): The cryptocurrency symbol (e.g., 'BTC-USD').

    Returns:
        str: An HTML string of the Plotly graph.
    """
    logging.info(f"Fetching data for symbol: {symbol}")
    
    try:
        data = yf.download(symbol, period="max", interval="1d")
        if data.empty:
            logging.error(f"No data found for symbol: {symbol}")
            raise ValueError("No data found for the specified symbol.")
    except Exception as e:
        logging.error(f"Error fetching data from yfinance: {e}")
        raise

    # Prepare data for Prophet
    df = pd.DataFrame()
    df['ds'] = data.index.values
    df['y'] = data['Close'].values

    # Train Prophet model
    logging.info("Training Prophet model...")
    model = Prophet()
    model.fit(df)

    # Make a 30-day forecast
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    logging.info("Forecast completed.")

    # Create Plotly figure
    fig = go.Figure()

    # Add historical data
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines',
        name='Historical Price'
    ))

    # Add forecast data
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        mode='lines',
        name='Forecasted Price',
        line=dict(color='orange')
    ))

    # Add uncertainty interval
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        fill=None,
        mode='lines',
        line=dict(width=0),
        name='Lower Bound',
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        fill='tonexty',
        mode='lines',
        fillcolor='rgba(255, 165, 0, 0.2)',
        line=dict(width=0),
        name='Uncertainty Interval',
        showlegend=False
    ))

    # Layout styling
    fig.update_layout(
        title={
            'text': f'Τιμή & Πρόβλεψη για {symbol}',
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title='Ημερομηνία',
        yaxis_title='Τιμή ($)',
        template='plotly_white',
        hovermode='x unified',
        legend_title='Δεδομένα',
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(family='Inter', size=12, color='rgb(51, 65, 85)')
    )

    # Use plotly.offline.plot to create a standalone HTML div
    plot_html = plot(
        fig, 
        output_type='div',
        include_plotlyjs=True,  # This will embed the necessary Plotly JS library
        config={'displayModeBar': False}
    )

    logging.info("Plotly plot HTML string generated successfully.")
    return plot_html

if __name__ == '__main__':
    # This part will not run in the web service, but is useful for local testing
    plot_div = get_prediction_plot('BTC-USD')
    print(plot_div)
