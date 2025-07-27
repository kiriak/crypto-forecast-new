# web_dashboard.py

from flask import Flask, render_template, Response, jsonify
import crypto_forecast
import json
from datetime import datetime
import logging
import pandas as pd
import base64

# Configure logging for the Flask application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """
    The main route of the application. Renders the index.html file.
    Data will be fetched by JavaScript from a separate API endpoint.
    """
    logging.info("Request for the main page ('/'). Rendering index.html.")
    try:
        # We only pass last_updated for display in the initial HTML.
        # Forecast data will be fetched via AJAX.
        last_updated = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return render_template('index.html', last_updated=last_updated)
    except Exception as e:
        logging.error(f"Error rendering the initial page: {e}")
        return render_template('error.html', error_message=f"An error occurred: {e}")

@app.route('/api/forecast_data_encoded')
def get_encoded_forecast_data():
    """
    API endpoint to retrieve Base64 encoded forecast data.
    """
    logging.info("Request for encoded forecast data API ('/api/forecast_data_encoded').")
    try:
        forecast_data = crypto_forecast.get_all_crypto_forecasts()
        logging.info("Forecast data retrieved for API endpoint.")

        processed_forecast_data = {}
        for ticker, data in forecast_data.items():
            processed_forecast_data[ticker] = {
                'current_price': data['current_price'],
                'forecast': []
            }
            if 'forecast' in data and data['forecast']:
                for entry in data['forecast']:
                    ds_value = entry['ds']
                    if isinstance(ds_value, (datetime, pd.Timestamp)):
                        ds_value = ds_value.isoformat()
                    else:
                        ds_value = str(ds_value)
                    
                    processed_forecast_data[ticker]['forecast'].append({
                        'ds': ds_value,
                        'yhat': entry['yhat'],
                        'yhat_lower': entry['yhat_lower'],
                        'yhat_upper': entry['yhat_upper']
                    })

        json_string = json.dumps(processed_forecast_data)
        encoded_forecast_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        logging.info("Forecast data encoded to Base64 and ready for API response.")
        
        # Return as JSON response
        return jsonify({"data": encoded_forecast_data})

    except Exception as e:
        logging.error(f"Error generating encoded forecast data: {e}")
        return jsonify({"error": "Failed to retrieve forecast data", "details": str(e)}), 500

@app.route('/health')
def health_check():
    """
    Health check for Render.com
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
