# web_dashboard.py

from flask import Flask, render_template, Response
import crypto_forecast
import json
from datetime import datetime
import logging
import pandas as pd # Import pandas for Timestamp check
import base64 # Import base64 for encoding

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

        # Process data to ensure datetime objects are converted to ISO format strings
        processed_forecast_data = {}
        for ticker, data in forecast_data.items():
            processed_forecast_data[ticker] = {
                'current_price': data['current_price'],
                'forecast': []
            }
            if 'forecast' in data and data['forecast']:
                for entry in data['forecast']:
                    ds_value = entry['ds']
                    # Convert pandas Timestamp or datetime objects to ISO format string
                    if isinstance(ds_value, (datetime, pd.Timestamp)):
                        ds_value = ds_value.isoformat()
                    else:
                        ds_value = str(ds_value) # Fallback to string if not datetime/Timestamp
                    
                    processed_forecast_data[ticker]['forecast'].append({
                        'ds': ds_value,
                        'yhat': entry['yhat'],
                        'yhat_lower': entry['yhat_lower'],
                        'yhat_upper': entry['yhat_upper']
                    })

        # --- ΝΕΟ: Κωδικοποίηση των δεδομένων JSON σε Base64 ---
        # Μετατροπή του dictionary σε JSON string
        json_string = json.dumps(processed_forecast_data)
        # Κωδικοποίηση του JSON string σε Base64
        # Χρησιμοποιούμε .encode('utf-8') για να μετατρέψουμε το string σε bytes
        # και .decode('utf-8') για να μετατρέψουμε το Base64 bytes πίσω σε string για το template
        encoded_forecast_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        logging.info("Forecast data encoded to Base64.")

        return render_template('index.html',
                               forecast_data=processed_forecast_data, # Για τον πίνακα Jinja2
                               encoded_forecast_data=encoded_forecast_data, # Για το JavaScript (Base64)
                               last_updated=last_updated)
    except Exception as e:
        logging.error(f"Σφάλμα κατά την απόδοση της σελίδας: {e}")
        # Return an error page or a simple message
        return render_template('error.html', error_message=f"Προέκυψε σφάλμα: {e}")

@app.route('/health')
def health_check():
    """
    Health check for Render.com
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
