
# web_dashboard.py

from flask import Flask, render_template, Response
import crypto_forecast # Επαναφορά του import
import json
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
        # Θα καλέσουμε το crypto_forecast.get_all_crypto_forecasts() εδώ
        # για να δούμε αν αυτό προκαλεί το πρόβλημα.
        forecast_data = crypto_forecast.get_all_crypto_forecasts()
        last_updated = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logging.info(f"Forecast data retrieved. Last updated: {last_updated}")

        # Για αυτή τη δοκιμή, θα επιστρέψουμε απλά ένα μήνυμα
        # που να επιβεβαιώνει ότι τα δεδομένα ανακτήθηκαν.
        # Δεν θα αποδώσουμε ακόμα το πλήρες HTML template.
        return f"Hello, World! Η εφαρμογή Flask λειτουργεί! Δεδομένα προβλέψεων ανακτήθηκαν για: {list(forecast_data.keys())}. Τελευταία ενημέρωση: {last_updated}"
    except Exception as e:
        logging.error(f"Σφάλμα κατά την ανάκτηση δεδομένων προβλέψεων: {e}")
        return f"Σφάλμα κατά την ανάκτηση δεδομένων: {e}"

@app.route('/health')
def health_check():
    """
    Health check for Render.com
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
