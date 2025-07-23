# web_dashboard.py

from flask import Flask, render_template, Response
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
        for ticker, data in forecast_data.items():
            if 'forecast' in data and data['forecast']:
                for entry in data['forecast']:
                    if isinstance(entry['ds'], datetime):
                        entry['ds'] = entry['ds'].isoformat() # ISO format για JavaScript

        return render_template('index.html',
                               forecast_data=forecast_data,
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
