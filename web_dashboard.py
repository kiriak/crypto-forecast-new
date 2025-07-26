# web_dashboard.py

from flask import Flask, render_template, Response
import crypto_forecast
import json # Προσθήκη για χειροκίνητη μετατροπή σε JSON
from datetime import datetime
import logging

# Ρύθμιση logging για την εφαρμογή Flask
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    """
    Η κύρια διαδρομή της εφαρμογής. Ανακτά τις προβλέψεις κρυπτονομισμάτων
    και τις αποδίδει στο αρχείο index.html.
    """
    logging.info("Αίτημα για την κύρια σελίδα ('/').")
    try:
        # Λήψη όλων των προβλέψεων κρυπτονομισμάτων
        forecast_data = crypto_forecast.get_all_crypto_forecasts()
        last_updated = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logging.info(f"Δεδομένα προβλέψεων ανακτήθηκαν. Τελευταία ενημέρωση: {last_updated}")

        # Μετατροπή των αντικειμένων datetime σε string για να είναι συμβατά με το JSON (για Plotly)
        # Αυτό είναι κρίσιμο για τη μεταφορά δεδομένων από την Python στο JavaScript
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

        # Χειροκίνητη μετατροπή σε JSON string εδώ
        # Αυτό διασφαλίζει ότι το JSON είναι σωστά διαμορφωμένο πριν περάσει στο template
        json_forecast_data_string = json.dumps(processed_forecast_data)

        return render_template('index.html',
                               forecast_data=processed_forecast_data, # Για τον πίνακα Jinja2
                               forecast_data_json_string=json_forecast_data_string, # Για το JavaScript
                               last_updated=last_updated)
    except Exception as e:
        logging.error(f"Σφάλμα κατά την απόδοση της σελίδας: {e}")
        # Επιστροφή μιας σελίδας σφάλματος ή ενός απλού μηνύματος
        return render_template('error.html', error_message=f"Προέκυψε σφάλμα: {e}")

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
