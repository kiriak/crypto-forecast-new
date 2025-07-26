# web_dashboard.py

from flask import Flask, render_template, Response, jsonify
import crypto_forecast # Ακόμα το εισάγουμε για το /api/forecast_data
import json
from datetime import datetime
import logging

# Ρύθμιση logging για την εφαρμογή Flask
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """
    Η κύρια διαδρομή της εφαρμογής. Επιστρέφει ένα απλό μήνυμα για δοκιμή.
    ΔΕΝ ΚΑΛΕΙ το crypto_forecast.get_all_crypto_forecasts() εδώ.
    """
    logging.info("Αίτημα για την κύρια σελίδα ('/'). Επιστρέφω απλό κείμενο.")
    return "Η εφαρμογή Flask λειτουργεί! Αυτή είναι μια πολύ απλή δοκιμή."

@app.route('/api/forecast_data')
def get_forecast_data():
    """
    API endpoint για την ανάκτηση δεδομένων πρόβλεψης σε μορφή JSON.
    Αυτό το endpoint θα συνεχίσει να καλεί το crypto_forecast.
    """
    logging.info("Αίτημα για δεδομένα API ('/api/forecast_data').")
    try:
        logging.info("Καλώντας crypto_forecast.get_all_crypto_forecasts() για API.")
        forecast_data = crypto_forecast.get_all_crypto_forecasts()
        logging.info("Ολοκληρώθηκε η κλήση crypto_forecast.get_all_crypto_forecasts() για API.")

        # Μετατροπή των αντικειμένων datetime σε string για να είναι συμβατά με το JSON
        processed_forecast_data = {}
        for ticker, data in forecast_data.items():
            processed_forecast_data[ticker] = {
                'current_price': data['current_price'],
                'forecast': []
            }
            if 'forecast' in data and data['forecast']:
                for entry in data['forecast']:
                    # Ελέγξτε αν το 'ds' είναι αντικείμενο datetime ή Timestamp πριν το isoformat
                    ds_value = entry['ds']
                    if isinstance(ds_value, datetime) or isinstance(ds_value, pd.Timestamp):
                        ds_value = ds_value.isoformat()
                    else:
                        ds_value = str(ds_value) # Fallback σε string αν δεν είναι datetime
                    
                    processed_forecast_data[ticker]['forecast'].append({
                        'ds': ds_value,
                        'yhat': entry['yhat'],
                        'yhat_lower': entry['yhat_lower'],
                        'yhat_upper': entry['yhat_upper']
                    })
        
        logging.info("Επιτυχής επεξεργασία δεδομένων πρόβλεψης σε JSON.")
        return jsonify(processed_forecast_data)
    except Exception as e:
        logging.error(f"Σφάλμα κατά την ανάκτηση ή επεξεργασία δεδομένων API: {e}")
        return jsonify({"error": "Failed to retrieve forecast data", "details": str(e)}), 500

@app.route('/health')
def health_check():
    """
    Έλεγχος υγείας για το Render.com
    """
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
