# web_dashboard.py

from flask import Flask, render_template, Response, jsonify
import crypto_forecast
import json
from datetime import datetime
import logging

# Ρύθμιση logging για την εφαρμογή Flask
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """
    Η κύρια διαδρομή της εφαρμογής. Απλώς αποδίδει το αρχικό index.html.
    Τα δεδομένα θα ανακτηθούν μέσω API.
    """
    logging.info("Αίτημα για την κύρια σελίδα ('/').")
    last_updated = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Προσπαθούμε να πάρουμε τα δεδομένα πρόβλεψης για να τα περάσουμε στο template
    # ακόμα και αν το API endpoint θα τα ανακτήσει ξανά.
    # Αυτό είναι για την περίπτωση που θέλουμε να ενσωματώσουμε τα δεδομένα απευθείας στο HTML.
    # Προς το παρόν, το index.html θα τα τραβήξει μέσω API, αλλά το Flask χρειάζεται
    # να περάσει κάτι για το {{ forecast_data | tojson | safe }}
    try:
        logging.info("Καλώντας crypto_forecast.get_all_crypto_forecasts() για αρχική φόρτωση.")
        forecast_data_for_template = crypto_forecast.get_all_crypto_forecasts()
        logging.info("Ολοκληρώθηκε η κλήση crypto_forecast.get_all_crypto_forecasts().")

        # Μετατροπή των αντικειμένων datetime σε string για να είναι συμβατά με το JSON
        processed_forecast_data_for_template = {}
        for ticker, data in forecast_data_for_template.items():
            processed_forecast_data_for_template[ticker] = {
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
                    
                    processed_forecast_data_for_template[ticker]['forecast'].append({
                        'ds': ds_value,
                        'yhat': entry['yhat'],
                        'yhat_lower': entry['yhat_lower'],
                        'yhat_upper': entry['yhat_upper']
                    })
        logging.info("Ολοκληρώθηκε η επεξεργασία δεδομένων για το template.")
    except Exception as e:
        logging.error(f"Σφάλμα κατά την προετοιμασία δεδομένων για το template: {e}")
        processed_forecast_data_for_template = {} # Επιστροφή κενού dictionary σε περίπτωση σφάλματος

    return render_template('index.html', 
                           last_updated=last_updated,
                           forecast_data=processed_forecast_data_for_template)

@app.route('/api/forecast_data')
def get_forecast_data():
    """
    API endpoint για την ανάκτηση δεδομένων πρόβλεψης σε μορφή JSON.
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
