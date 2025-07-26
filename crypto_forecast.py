import yfinance as yf # Ακόμα χρειάζεται για την εγκατάσταση, αλλά δεν χρησιμοποιείται για λήψη δεδομένων
from prophet import Prophet
import pandas as pd
from datetime import date, timedelta
import logging
import json

# Ρύθμιση logging για το module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Αφαιρούμε την get_crypto_data καθώς δεν θα χρησιμοποιούμε πλέον yfinance για λήψη δεδομένων

def create_demo_data(ticker, start_date, end_date):
    """
    Δημιουργεί demo δεδομένα για δοκιμαστικούς σκοπούς, προσομοιώνοντας ιστορικές τιμές.
    Προστίθεται μια μικρή διακύμανση ανάλογα με το ticker.
    """
    logging.info(f"Δημιουργία demo δεδομένων για {ticker}.")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    base_price = 0
    if ticker == "BTC-USD":
        base_price = 20000
        volatility = 500
    elif ticker == "ETH-USD":
        base_price = 1500
        volatility = 100
    elif ticker == "SOL-USD":
        base_price = 30
        volatility = 5
    else:
        base_price = 100
        volatility = 10

    # Δημιουργία πιο ρεαλιστικών demo δεδομένων
    prices = []
    current_val = base_price
    for i in range(len(dates)):
        change = (i % 20 - 10) * (volatility / 100) + (i / 365) * (base_price / 10) # Τάση + διακύμανση
        current_val += change
        prices.append(max(1, current_val)) # Να μην πέφτει κάτω από 1
    
    data = {
        'Date': dates,
        'Close': prices
    }
    df = pd.DataFrame(data)
    df = df.set_index('Date') # Ορισμός της ημερομηνίας ως index
    logging.info(f"Επιτυχής δημιουργία demo δεδομένων για {ticker}.")
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
    Τώρα χρησιμοποιεί μόνο demo δεδομένα για να αποφύγει προβλήματα με το yfinance.
    """
    cryptos = ["BTC-USD", "ETH-USD", "SOL-USD"]
    all_forecasts = {}

    end_date = date.today()
    start_date = end_date - timedelta(days=365 * 2) # 2 χρόνια demo δεδομένων

    for ticker in cryptos:
        logging.info(f"Επεξεργασία {ticker} με demo δεδομένα...")
        # Χρησιμοποιούμε πάντα demo δεδομένα
        data = create_demo_data(ticker, start_date, end_date)
        
        # Λήψη της τρέχουσας τιμής (τελευταία διαθέσιμη τιμή από τα demo δεδομένα)
        current_price = 0
        if not data.empty and 'Close' in data.columns and not data['Close'].isnull().iloc[-1]:
            current_price = data['Close'].iloc[-1]
        else:
            logging.warning(f"Αδυναμία ανάκτησης τρέχουσας τιμής από demo δεδομένα για {ticker}. Ορίζεται σε 0.")

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
