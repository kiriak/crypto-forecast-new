# web_dashboard.py

from flask import Flask, render_template, Response
import crypto_forecast
import json # Import the json module
from datetime import datetime
import logging

# Configure logging for the Flask application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """
    The main route of the application. Retrieves cryptocurrency forecasts
    and renders them to the index.html file.
    """
    logging.info("Request for the main page ('/').")
    try:
        # Retrieve all cryptocurrency forecasts
        forecast_data = crypto_forecast.get_all_crypto_forecasts()
        last_updated = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logging.info(f"Forecast data retrieved. Last updated: {last_updated}")

        # Convert datetime objects to string for JSON compatibility (for Plotly)
        # This is crucial for transferring data from Python to JavaScript
        processed_forecast_data = {}
        for ticker, data in forecast_data.items():
            processed_forecast_data[ticker] = {
                'current_price': data['current_price'],
                'forecast': []
            }
            if 'forecast' in data and data['forecast']:
                for entry in data['forecast']:
                    # Check if 'ds' is a datetime or Timestamp object before isoformat
                    ds_value = entry['ds']
                    if isinstance(ds_value, datetime) or isinstance(ds_value, pd.Timestamp):
                        ds_value = ds_value.isoformat()
                    else:
                        ds_value = str(ds_value) # Fallback to string if not datetime
                    
                    processed_forecast_data[ticker]['forecast'].append({
                        'ds': ds_value,
                        'yhat': entry['yhat'],
                        'yhat_lower': entry['yhat_lower'],
                        'yhat_upper': entry['yhat_upper']
                    })

        # Manually convert to JSON string here
        # This ensures the JSON is correctly formatted before passing to the template
        json_forecast_data_string = json.dumps(processed_forecast_data)

        return render_template('index.html',
                               forecast_data=processed_forecast_data, # For the Jinja2 table
                               forecast_data_json_string=json_forecast_data_string, # For JavaScript
                               last_updated=last_updated)
    except Exception as e:
        logging.error(f"Error rendering the page: {e}")
        # Return an error page or a simple message
        return render_template('error.html', error_message=f"An error occurred: {e}")

@app.route('/health')
def health_check():
    """
    Health check for Render.com
    """
    return "OK", 200

if __name__ == '__main__':
    # For local development, run the application in debug mode
    # On Render.com, gunicorn will be used
    app.run(debug=True, host='0.0.0.0', port=5000)
