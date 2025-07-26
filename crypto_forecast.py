import yfinance as yf
from prophet import Prophet
import pandas as pd
from datetime import date, timedelta
import logging

# Ρύθμιση logging για το module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_crypto_data(ticker="BTC-USD", period="6mo"):
    """
    Ανακτά ιστορικά δεδομένα κρυπτονομισμάτων από το Yahoo Finance.
    Προσθέτει χειρισμό σφαλμάτων και επιστρέφει κενό DataFrame σε περίπτωση αποτυχίας.
    """
    try:
        data = yf.download(ticker, period=period)
        if data.empty:
            logging.warning(f"Δεν βρέθηκαν δεδομένα για {ticker}. Επιστροφή κενού DataFrame.")
            return pd.DataFrame()
        logging.info(f"Επιτυχής ανάκτηση δεδομένων για {ticker}.")
        return data
    except Exception as e:
        logging.error(f"Σφάλμα κατά την ανάκτηση δεδομένων για {ticker}: {e}")
        return pd.DataFrame()

def create_demo_data(start_date, end_date):
    """
    Δημιουργεί demo δεδομένα για δοκιμαστικούς σκοπούς.
    """
    logging.warning("Δημιουργία demo δεδομένων.")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    data = {
        'ds': dates,
        'y': [100 + i * 0.5 + (i % 10 - 5) * 2 for i in range(len(dates))]
    }
    df = pd.DataFrame(data)
    return df

def train_and_predict(df):
    """
    Εκπαιδεύει το μοντέλο Prophet και κάνει προβλέψεις.
    """
    if df.empty:
        logging.error("Κενό DataFrame για εκπαίδευση μοντέλου. Αδυναμία πρόβλεψης.")
        return None

    # Προετοιμασία δεδομένων για το Prophet
    # Το Prophet αναμένει στήλες 'ds' (ημερομηνία) και 'y' (τιμή)
    df_prophet = df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

    # Εξασφάλιση ότι η στήλη 'ds' είναι datetime και timezone-aware (ή naive με συγκεκριμένο τρόπο)
    # Εδώ θα εφαρμόσουμε μια ζώνη ώρας ή θα την κάνουμε naive αν είναι ήδη timezone-aware
    if pd.api.types.is_datetime64tz_dtype(df_prophet['ds']):
        # Αν είναι ήδη timezone-aware, μετατρέψτε το σε naive UTC
        df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
    elif pd.api.types.is_datetime64_ns_dtype(df_prophet['ds']):
        # Αν είναι naive, βεβαιωθείτε ότι είναι σε UTC για συνέπεια
        # ή εφαρμόστε μια συγκεκριμένη ζώνη ώρας αν είναι απαραίτητο
        # Για παράδειγμα, μπορείτε να το κάνετε timezone-aware:
        # df_prophet['ds'] = df_prophet['ds'].dt.tz_localize('UTC')
        # Ή να βεβαιωθείτε ότι είναι απλά naive:
        pass # Αφήστε το ως έχει αν είναι ήδη naive και το Prophet το χειρίζεται

    # Απενεργοποίηση ετήσιας εποχικότητας αν τα δεδομένα δεν καλύπτουν αρκετό διάστημα
    # για να αποφύγουμε warnings ή σφάλματα.
    # Το Prophet χρειάζεται τουλάχιστον 2 κύκλους για την ετήσια εποχικότητα.
    yearly_seasonality = True
    if len(df_prophet['ds'].dt.year.unique()) < 2: # Αν έχουμε δεδομένα για λιγότερο από 2 χρόνια
        yearly_seasonality = False
        logging.info("Απενεργοποίηση ετήσιας εποχικότητας. Τρέξτε το Prophet με yearly_seasonality=True για να το παρακάμψετε.")

    # Εκπαίδευση του μοντέλου
    model = Prophet(yearly_seasonality=yearly_seasonality)
    model.fit(df_prophet)
    logging.info("Επιτυχής εκπαίδευση μοντέλου Prophet.")

    # Δημιουργία μελλοντικού DataFrame για προβλέψεις
    future = model.make_future_dataframe(periods=180) # Πρόβλεψη για 180 ημέρες (περίπου 6 μήνες)
    
    # Εξασφάλιση ότι η στήλη 'ds' του future DataFrame είναι επίσης timezone-naive
    if pd.api.types.is_datetime64tz_dtype(future['ds']):
        future['ds'] = future['ds'].dt.tz_localize(None)

    # Πρόβλεψη
    forecast = model.predict(future)
    logging.info("Επιτυχής πρόβλεψη με μοντέλο Prophet.")
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def get_all_crypto_forecasts():
    """
    Ανακτά δεδομένα και κάνει προβλέψεις για μια λίστα κρυπτονομισμάτων.
    """
    cryptos = ["BTC-USD", "ETH-USD", "SOL-USD"] # Προσθήκη SOL-USD
    all_forecasts = {}

    for ticker in cryptos:
        logging.info(f"Επεξεργασία {ticker}...")
        data = get_crypto_data(ticker)
        
        if data.empty:
            logging.warning(f"Δεν βρέθηκαν πραγματικά δεδομένα για {ticker}. Επιστροφή demo δεδομένων.")
            # Δημιουργία demo δεδομένων για να μην κρασάρει η εφαρμογή
            end_date = date.today()
            start_date = end_date - timedelta(days=365 * 2) # 2 χρόνια demo δεδομένων
            demo_df = create_demo_data(start_date, end_date)
            demo_df = demo_df.rename(columns={'ds': 'Date', 'y': 'Close'}).set_index('Date')
            data = demo_df # Χρησιμοποιούμε τα demo δεδομένα

        # Λήψη της τρέχουσας τιμής (τελευταία διαθέσιμη τιμή)
        current_price = data['Close'].iloc[-1] if not data.empty else 0

        # Εκπαίδευση και πρόβλεψη
        forecast_df = train_and_predict(data)

        if forecast_df is not None:
            all_forecasts[ticker] = {
                "current_price": current_price,
                "forecast": forecast_df.to_dict(orient='records')
            }
            logging.info(f"Ολοκληρώθηκε η πρόβλεψη για {ticker}.")
        else:
            all_forecasts[ticker] = {
                "current_price": current_price,
                "forecast": [] # Επιστροφή κενού λίστας αν η πρόβλεψη απέτυχε
            }
            logging.error(f"Αδυναμία πρόβλεψης για {ticker}.")

    return all_forecasts

if __name__ == '__main__':
    # Παράδειγμα χρήσης
    forecasts = get_all_crypto_forecasts()
    for ticker, data in forecasts.items():
        print(f"\n--- {ticker} ---")
        print(f"Τρέχουσα τιμή: ${data['current_price']:.2f}")
        if data['forecast']:
            print("Πρόβλεψη (τελευταία 5 σημεία):")
            for entry in data['forecast'][-5:]:
                print(f"  Ημερομηνία: {entry['ds'].split('T')[0]}, Πρόβλεψη: ${entry['yhat']:.2f}, Κάτω: ${entry['yhat_lower']:.2f}, Άνω: ${entry['yhat_upper']:.2f}")
        else:
            print("Δεν υπάρχουν δεδομένα πρόβλεψης.")
