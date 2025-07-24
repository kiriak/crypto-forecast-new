# web_dashboard.py

from flask import Flask, render_template, Response, jsonify # Προσθήκη jsonify
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
    # Δεν χρειάζεται να περάσουμε forecast_data εδώ, καθώς θα το φέρει το JS
    last_updated = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template('index.html', last_updated=last_updated)

@app.route('/api/forecast_data')
def get_forecast_data():
    """
    Νέο API endpoint για την ανάκτηση δεδομένων πρόβλεψης σε μορφή JSON.
    """
    logging.info("Αίτημα για δεδομένα API ('/api/forecast_data').")
    try:
        forecast_data = crypto_forecast.get_all_crypto_forecasts()

        # Μετατροπή των αντικειμένων datetime σε string για να είναι συμβατά με το JSON
        processed_forecast_data = {}
        for ticker, data in forecast_data.items():
            processed_forecast_data[ticker] = {
                'current_price': data['current_price'],
                'forecast': []
            }
            if 'forecast' in data and data['forecast']:
                for entry in data['forecast']:
                    processed_forecast_data[ticker]['forecast'].append({
                        'ds': entry['ds'].isoformat() if isinstance(entry['ds'], datetime) else str(entry['ds']),
                        'yhat': entry['yhat'],
                        'yhat_lower': entry['yhat_lower'],
                        'yhat_upper': entry['yhat_upper']
                    })
        
        # Επιστροφή των επεξεργασμένων δεδομένων ως JSON response
        logging.info("Επιτυχής επιστροφή δεδομένων πρόβλεψης ως JSON.")
        return jsonify(processed_forecast_data)
    except Exception as e:
        logging.error(f"Σφάλμα κατά την ανάκτηση δεδομένων API: {e}")
        return jsonify({"error": "Failed to retrieve forecast data", "details": str(e)}), 500

@app.route('/health')
def health_check():
    """
    Έλεγχος υγείας για το Render.com
    """
    return "OK", 200

if __name__ == '__main__':
    # Για τοπική ανάπτυξη, τρέξτε την εφαρμογή σε debug mode
    # Στο Render.com, θα χρησιμοποιηθεί το gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
