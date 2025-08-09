import os
import logging
from flask import Flask, render_template, request, jsonify, make_response
import datetime
from plotly.offline import plot
import plotly.graph_objects as go
import pandas as pd
import time
import requests

# Assuming crypto_forecast is a module in the same directory
# from crypto_forecast import get_crypto_data, generate_forecast_plot

# Placeholder functions for get_crypto_data and generate_forecast_plot
# In your actual project, these would be imported from the crypto_forecast.py file
# For this example, we will use placeholders to ensure the Flask app is runnable
def get_crypto_data(symbol='BTC-USD'):
    """
    Simulates fetching crypto data for a given symbol.
    In a real app, this would get data from an API.
    """
    logging.info(f"Simulating data fetch for {symbol}...")
    
    # Simple check for a valid symbol
    if symbol not in ['BTC-USD', 'ETH-USD', 'DOGE-USD', 'SOL-USD', 'ADA-USD']:
        return pd.DataFrame() # Return empty DataFrame if symbol is invalid
        
    # Generate some dummy data for demonstration
    dates = pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='D'))
    prices = [100 + i * 2 * (1 + 0.1 * (i % 10)) for i in range(100)]
    df = pd.DataFrame({'ds': dates, 'y': prices})
    return df

def generate_forecast_plot(data, symbol='BTC-USD'):
    """
    Simulates generating a Plotly forecast plot.
    """
    logging.info(f"Simulating forecast plot generation for {symbol}...")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['ds'], y=data['y'], mode='lines', name='Historical Prices'))

    # Add a simple forecast line
    forecast_dates = pd.to_datetime(pd.date_range(start=data['ds'].iloc[-1], periods=30, freq='D'))
    forecast_prices = [data['y'].iloc[-1] * (1 + 0.01 * i) for i in range(30)]
    fig.add_trace(go.Scatter(x=forecast_dates, y=forecast_prices, mode='lines', name='Forecast', line=dict(dash='dash')))
    
    fig.update_layout(
        title=f'{symbol} Price Forecast',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        template='plotly_white',
        xaxis_rangeslider_visible=True,
    )
    return fig


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting Flask application...")

app = Flask(__name__, template_folder='templates')

# Check if required environment variables are set
if not os.environ.get("RENDER"):
    logging.warning("Not running on Render. Using a default port.")
    PORT = 8080
else:
    logging.info("Running on Render. Using PORT environment variable.")
    PORT = os.environ.get("PORT", 10000)

def create_error_plot(error_message):
    """
    Creates a simple Plotly figure with an error message.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error: {error_message}",
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=20, color="red")
    )
    fig.update_layout(
        title_text="Plot Generation Error",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis_visible=False,
        yaxis_visible=False
    )
    return fig

@app.route('/', methods=['GET'])
def index():
    """
    Handles the initial request for the main page.
    Renders the index.html template without a plot initially.
    """
    logging.info("Request for the main page ('/'). Rendering index.html.")
    now = datetime.datetime.now()
    last_updated_time = now.strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        'index.html',
        plot_html=None,
        last_updated=last_updated_time,
        current_coin='BTC-USD'
    )

@app.route('/forecast', methods=['POST'])
def forecast():
    """
    Handles the POST request to generate a forecast.
    It receives the coin symbol from the frontend, generates the plot,
    and returns the plot's HTML as a JSON response.
    """
    logging.info("Request for a new forecast received.")
    
    # Get the coin symbol from the JSON request
    selected_coin = request.json.get('coin_symbol', 'BTC-USD')
    logging.info(f"Generating forecast for: {selected_coin}")

    try:
        # Step 1: Get the data
        # This function would be imported from crypto_forecast.py
        data = get_crypto_data(symbol=selected_coin)
        
        if data is None or data.empty:
            error_message = f"Δεν βρέθηκαν δεδομένα για το σύμβολο: {selected_coin}. Παρακαλώ δοκιμάστε ένα άλλο σύμβολο."
            logging.error(error_message)
            fig = create_error_plot(error_message)
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            return jsonify({'plot_html': plot_html, 'error': error_message})
        else:
            # Step 2: Generate the plot
            # This function would be imported from crypto_forecast.py
            fig = generate_forecast_plot(data, symbol=selected_coin)
            
            # Step 3: Convert the plot to HTML
            plot_html = plot(
                fig,
                output_type='div',
                include_plotlyjs=True,
                config={'displayModeBar': False}
            )
            logging.info("Η HTML του γραφήματος δημιουργήθηκε με επιτυχία.")
            return jsonify({'plot_html': plot_html, 'error': None})

    except Exception as e:
        # Catch any errors during the proc
