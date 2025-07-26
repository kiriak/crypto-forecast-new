# web_dashboard.py

from flask import Flask, render_template, Response
import crypto_forecast
import json # Still needed for potential future use or if jsonify is explicitly used
from datetime import datetime
import logging
import pandas as pd # Import pandas for Timestamp check

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
        # This is done here to ensure the data is JSON-serializable for both Jinja's tojson
        # and direct Python usage if needed.
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

        # Pass the processed_forecast_data directly. Jinja's tojson filter will handle the conversion
        # and safe escaping within the template.
        return render_template('index.html',
                               forecast_data=processed_forecast_data, # For the Jinja2 table
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
