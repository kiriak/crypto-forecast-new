import yfinance as yf
from prophet import Prophet
import pandas as pd
from datetime import date, timedelta
import logging
import json # Προσθήκη για χειρισμό JSONDecodeError

# Ρύθμιση logging για το module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_crypto_data(ticker="BTC-USD", period="6mo"):
    """
    Ανακτά ιστορικά δεδομένα κρυπτονομισμάτων από το Yahoo Finance.
    Προσθέτει χειρισμό σφαλμάτων και επιστρέφει κενό DataFrame σε περίπτωση αποτυχίας.
    """
    try:
        data = yf.download(ticker, period=period, progress=False, actions=False) # progress=False, actions=False για λιγότερο verbose output
        if data.empty:
            logging.warning(f"Δεν βρέθηκαν δεδομένα για {ticker} από το yfinance. Επιστροφή κενού DataFrame.")
            return pd.DataFrame()
        
        # Ελέγξτε αν η στήλη 'Close' υπάρχει και δεν είναι κενή
        if 'Close' not in data.columns or data['Close'].empty:
            logging.warning(f"Η στήλη 'Close' δεν βρέθηκε ή είναι κενή για {ticker}. Επιστροφή κενού DataFrame.")
            return pd.DataFrame()

        logging.info(f"Επιτυχής ανάκτηση δεδομένων για {ticker}.")
        return data
    except json.JSONDecodeError as e:
        logging.error(f"JSONDecodeError κατά την ανάκτηση δεδομένων για {ticker}: {e}. Πιθανώς λανθασμένη απάντηση από τον server.")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Γενικό σφάλμα κατά την ανάκτηση δεδομένων για {ticker}: {e}")
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
    if df.empty or 'Close' not in df.columns or df['Close'].isnull().all():
        logging.error("Κενό ή μη έγκυρο DataFrame για εκπαίδευση μοντέλου. Αδυναμία πρόβλεψης.")
        return None

    # Προετοιμασία δεδομένων για το Prophet
    df_prophet = df.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

    # Εξασφάλιση ότι η στήλη 'ds' είναι datetime και timezone-naive (απαραίτητο για Prophet)
    if pd.api.types.is_datetime64tz_dtype(df_prophet['ds']):
        df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)
    
    # Απενεργοποίηση ετήσιας εποχικότητας αν τα δεδομένα δεν καλύπτουν αρκετό διάστημα
    yearly_seasonality = True
    if len(df_prophet['ds'].dt.year.unique()) < 2:
        yearly_seasonality = False
        logging.info("Απενεργοποίηση ετήσιας εποχικότητας. Τρέξτε το Prophet με yearly_seasonality=True για να το παρακάμψετε.")

    # Εκπαίδευση του μοντέλου
    model = Prophet(yearly_seasonality=yearly_seasonality)
    try:
        model.fit(df_prophet)
        logging.info("Επιτυχής εκπαίδευση μοντέλου Prophet.")
    except Exception as e:
        logging.error(f"Σφάλμα κατά την εκπαίδευση του μοντέλου Prophet: {e}")
        return None

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
    cryptos = ["BTC-USD", "ETH-USD", "SOL-USD"]
    all_forecasts = {}

    for ticker in cryptos:
        logging.info(f"Επεξεργασία {ticker}...")
        data = get_crypto_data(ticker)
        
        # Αν δεν βρεθούν πραγματικά δεδομένα ή είναι όλα NaN, χρησιμοποιήστε demo δεδομένα
        if data.empty or 'Close' not in data.columns or data['Close'].isnull().all():
            logging.warning(f"Δεν βρέθηκαν πραγματικά δεδομένα ή είναι όλα NaN για {ticker}. Επιστροφή demo δεδομένων.")
            end_date = date.today()
            start_date = end_date - timedelta(days=365 * 2) # 2 χρόνια demo δεδομένων
            demo_df = create_demo_data(start_date, end_date)
            demo_df = demo_df.rename(columns={'ds': 'Date', 'y': 'Close'}).set_index('Date')
            data = demo_df

        # Λήψη της τρέχουσας τιμής (τελευταία διαθέσιμη τιμή)
        # Ελέγξτε αν το DataFrame είναι κενό ή αν η τελευταία τιμή είναι NaN
        current_price = 0
        if not data.empty and 'Close' in data.columns and not data['Close'].isnull().iloc[-1]:
            current_price = data['Close'].iloc[-1]
        else:
            logging.warning(f"Αδυναμία ανάκτησης τρέχουσας τιμής για {ticker}. Ορίζεται σε 0.")

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
                # Ελέγξτε αν το 'ds' είναι αντικείμενο datetime πριν το split
                ds_str = entry['ds'].isoformat().split('T')[0] if isinstance(entry['ds'], pd.Timestamp) else str(entry['ds']).split('T')[0]
                print(f"  Ημερομηνία: {ds_str}, Πρόβλεψη: ${entry['yhat']:.2f}, Κάτω: ${entry['yhat_lower']:.2f}, Άνω: ${entry['yhat_upper']:.2f}")
        else:
            print("Δεν υπάρχουν δεδομένα πρόβλεψης.")
