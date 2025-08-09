import os
import logging
from flask import Flask, render_template, request, jsonify
import datetime
from plotly.offline import plot
import plotly.graph_objects as go
import pandas as pd
from prophet import Prophet
import json
import requests
import warnings
import time

# Suppress FutureWarning from Prophet
warnings.simplefilter(action='ignore', category=FutureWarning)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting Flask application...")

app = Flask(__name__, template_folder='templates')

# Check if running on Render for correct port
if not os.environ.get("RENDER"):
    logging.warning("Not running on Render. Using default port.")
    PORT = 8080
else:
    logging.info("Running on Render. Using PORT environment variable.")
    PORT = os.environ.get("PORT", 10000)

# ==============================================================================
# ATTENTION: ADD YOUR OWN API KEY FROM COINAPI HERE
# Get a free key at https://www.coinapi.io
# ==============================================================================
# CORRECTED LINE: API key must be a string, enclosed in quotes.
API_KEY = "f142a994-4800-4c42-8bf7-825f7bbcc932"

def get_crypto_data(symbol='BTC', period_days='730'):
    """
    Fetches historical cryptocurrency data from the CoinAPI.
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=int(period_days))
    
    url = f"https://rest.coinapi.io/v1/ohlcv/{symbol}/USD/history?period_id=1DAY&time_start={start_date.isoformat()}&time_end={end_date.isoformat()}"
    headers = {'X-CoinAPI-Key': API_KEY}

    retries = 3
    for i in range(retries):
        try:
            logging.info(f"Fetching data for symbol: {symbol} from CoinAPI (Attempt {i+1}/{retries})...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logging.warning(f"No data found for symbol {symbol} on attempt {i+1}. Retrying...")
                time.sleep(2)
                continue

            df = pd.DataFrame(data)
            df['time_close'] = pd.to_datetime(df['time_close'])
            df.rename(columns={'time_close': 'ds', 'price_close': 'y'}, inplace=True)
            return df
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from API on attempt {i+1}: {e}")
            time.sleep(2)
        except Exception as e:
            logging.error(f"General error processing data on attempt {i+1}: {e}")
            time.sleep(2)
    
    logging.error("Failed to fetch data after multiple attempts.")
    return pd.DataFrame()

def generate_forecast_plot(data, symbol='BTC', periods=180):
    """
    Generates a cryptocurrency price forecast plot using Prophet.
    """
    try:
        logging.info(f"Generating forecast plot for symbol: {symbol}...")
        
        m = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        m.fit(data)

        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)

        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['ds'],
            y=data['y'],
            mode='lines',
            name='Historical Prices',
            line=dict(color='#008080')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat'],
            mode='lines',
            name='Forecast',
            line=dict(color='#8A2BE2', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_upper'],
            mode='lines',
            name='Upper Bound',
            line=dict(color='rgba(138, 43, 226, 0.2)', width=0),
            fill=None
        ))
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            mode='lines',
            name='Lower Bound',
            fill='tonexty',
            fillcolor='rgba(138, 43, 226, 0.2)',
            line=dict(color='rgba(138, 43, 226, 0.2)', width=0)
        ))

        fig.update_layout(
            title=f'Price Forecast for {symbol.capitalize()} for the next {periods} days',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            template='plotly_white',
            xaxis_rangeslider_visible=True,
            showlegend=True
        )
        return fig
    except Exception as e:
        logging.error(f"Error generating forecast plot: {e}")
        return create_error_plot(f"Error: {e}")

def create_error_plot(error_message):
    """
    Creates a simple Plotly plot with an error message.
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
        title_text="Error Generating Plot",
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
    Returns index.html.
    """
    logging.info("Request for main page ('/'). Returning index.html.")
    now = datetime.datetime.now()
    last_updated_time = now.strftime("%Y-%m-%d %H:%M:%S")

    try:
        data = get_crypto_data(symbol='BTC')
        if data.empty:
            error_message = "Could not fetch data for Bitcoin. Please try another coin."
            fig = create_error_plot(error_message)
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            current_coin = 'Error'
        else:
            fig = generate_forecast_plot(data, symbol='BTC')
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            current_coin = 'BTC'
    except Exception as e:
        logging.error(f"Error in initial plot generation: {e}")
        fig = create_error_plot(str(e))
        plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
        current_coin = 'Error'

    return render_template(
        'index.html',
        plot_html=plot_html,
        last_updated=last_updated_time,
        current_coin=current_coin
    )

@app.route('/forecast', methods=['POST'])
def forecast():
    """
    Handles the POST request to generate a new forecast.
    Returns the plot's HTML as JSON.
    """
    logging.info("Received request for new forecast.")
    
    selected_coin = request.json.get('coin_symbol', 'BTC')
    logging.info(f"Generating forecast for: {selected_coin}")

    try:
        data = get_crypto_data(symbol=selected_coin)
        
        if data is None or data.empty:
            error_message = f"No data found for symbol: {selected_coin}. Please try another symbol."
            logging.error(error_message)
            fig = create_error_plot(error_message)
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            return jsonify({'plot_html': plot_html, 'error': error_message})
        else:
            fig = generate_forecast_plot(data, symbol=selected_coin)
            plot_html = plot(
                fig,
                output_type='div',
                include_plotlyjs=True,
                config={'displayModeBar': False}
            )
            logging.info("Plot HTML generated successfully.")
            return jsonify({'plot_html': plot_html, 'error': None})

    except Exception as e:
        logging.error(f"Error during plot generation: {e}")
        error_message = str(e)
        fig = create_error_plot(error_message)
        plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
        return jsonify({'plot_html': plot_html, 'error': error_message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
