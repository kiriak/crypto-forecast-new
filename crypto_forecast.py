
# crypto_forecast.py

import yfinance as yf
import pandas as pd
from prophet import Prophet
import logging

# Ρύθμιση logging για καλύτερη παρακολούθηση
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Λίστα κρυπτονομισμάτων για πρόβλεψη
CRYPTOS = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'XRP-USD', 'SOL-USD']

def fetch_crypto_data(ticker):
    """
    Ανακτά ιστορικά δεδομένα τιμών για ένα δεδομένο κρυπτονόμισμα.
    Χρησιμοποιεί το yfinance για να τραβήξει δεδομένα για το μέγιστο δυνατό διάστημα.
    """
    try:
        logging.info(f"Ανάκτηση δεδομένων για: {ticker}")
        # Ανάκτηση δεδομένων για το μέγιστο δυνατό διάστημα ('max')
        data = yf.download(ticker, period="max")
        if data.empty:
            logging.warning(f"Δεν βρέθηκαν δεδομένα για {ticker}. Ελέγξτε το σύμβολο.")
            return None
        # Χρησιμοποιούμε μόνο τη στήλη 'Close' για την πρόβλεψη
        df = data[['Close']].reset_index()
        df.columns = ['Date', 'Close']
        logging.info(f"Επιτυχής ανάκτηση {len(df)} γραμμών δεδομένων για {ticker}.")
        return df
    except Exception as e:
        logging.error(f"Σφάλμα κατά την ανάκτηση δεδομένων για {ticker}: {e}")
        return None

def predict_crypto_price(ticker, df):
    """
    Εκτελεί πρόβλεψη τιμών για ένα κρυπτονόμισμα χρησιμοποιώντας το Prophet.
    Προβλέπει τις τιμές για τους επόμενους 6 μήνες.
    """
    if df is None or df.empty:
        logging.warning(f"Δεν υπάρχουν δεδομένα για πρόβλεψη για {ticker}. Παράλειψη πρόβλεψης.")
        return None, None

    logging.info(f"Προετοιμασία δεδομένων για Prophet για: {ticker}")
    # Το Prophet απαιτεί στήλες 'ds' (χρονοσείρα) και 'y' (τιμή)
    df_prophet = df.rename(columns={'Date': 'ds', 'Close': 'y'})

    # Δημιουργία και εκπαίδευση του μοντέλου Prophet
    # Απενεργοποίηση μηνυμάτων 'The Prophet has spoken!'
    with suppress_stdout_stderr():
        model = Prophet(
            seasonality_mode='multiplicative',
            changepoint_prior_scale=0.05,
            daily_seasonality=True # Ενεργοποίηση καθημερινής εποχικότητας
        )
        model.fit(df_prophet)
    logging.info(f"Το μοντέλο Prophet εκπαιδεύτηκε για {ticker}.")

    # Δημιουργία DataFrame για μελλοντικές προβλέψεις (6 μήνες)
    future = model.make_future_dataframe(periods=6*30, freq='D') # 6 μήνες * ~30 ημέρες
    logging.info(f"Δημιουργήθηκε μελλοντικό DataFrame για 6 μήνες για {ticker}.")

    # Πραγματοποίηση προβλέψεων
    forecast = model.predict(future)
    logging.info(f"Οι προβλέψεις ολοκληρώθηκαν για {ticker}.")

    # Επιστροφή της τρέχουσας τιμής (τελευταία τιμή στα δεδομένα εκπαίδευσης)
    current_price = df['Close'].iloc[-1]

    # Επιστροφή του forecast DataFrame με τις στήλες ds, yhat, yhat_lower, yhat_upper
    return current_price, forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

# Βοηθητική κλάση για την καταστολή της εξόδου του Prophet (αποφεύγει τα "The Prophet has spoken!" μηνύματα)
import os
import sys
from contextlib import contextmanager

@contextmanager
def suppress_stdout_stderr():
    """
    Καταστέλλει την έξοδο stdout και stderr μέσα σε ένα block.
    Χρησιμοποιείται για να αποφευχθούν τα μηνύματα του Prophet.
    """
    with open(os.devnull, 'w') as fnull:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = fnull, fnull
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

if __name__ == '__main__':
    # Παράδειγμα χρήσης:
    print("Εκτέλεση crypto_forecast.py απευθείας για δοκιμή...")
    forecast_results = get_all_crypto_forecasts()
    if forecast_results:
        for ticker, data in forecast_results.items():
            print(f"\n--- {ticker} ---")
            print(f"Τρέχουσα τιμή: ${data['current_price']:.2f}")
            print("Πρόβλεψη για τις επόμενες 6 μήνες (τελευταίες 5 ημέρες πρόβλεψης):")
            # Εμφάνιση μόνο των 5 τελευταίων προβλέψεων για συντομία
            for entry in data['forecast'][-5:]:
                print(f"Ημερομηνία: {entry['ds'].split('T')[0]}, Πρόβλεψη: ${entry['yhat']:.2f}")
    else:
        print("Δεν ήταν δυνατή η λήψη προβλέψεων.")
