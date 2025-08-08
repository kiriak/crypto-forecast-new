import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import logging
import time

# Ρυθμίσεις για την καταγραφή (logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_crypto_data(symbol: str = "BTC-USD", period: str = "1y", interval: str = "1d"):
    """
    Ανακτά δεδομένα κρυπτονομισμάτων χρησιμοποιώντας το yfinance με exponential backoff για επαναλήψεις.
    Args:
        symbol (str): Το σύμβολο του κρυπτονομίσματος (ticker).
        period (str): Η χρονική περίοδος για τα δεδομένα (π.χ. "1y").
        interval (str): Το χρονικό διάστημα των δεδομένων (π.χ. "1d").
    Returns:
        pd.DataFrame: Ένα DataFrame με τα δεδομένα του κρυπτονομίσματος ή None αν η ανάκτηση αποτύχει.
    """
    logging.info(f"Ανάκτηση δεδομένων για το σύμβολο: {symbol}")
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            # Προσπάθεια λήψης δεδομένων
            data = yf.download(symbol, period=period, interval=interval)
            
            if data.empty:
                logging.error(f"Δεν βρέθηκαν δεδομένα για το καθορισμένο σύμβολο: {symbol}")
                return None

            return data
        except Exception as e:
            retries += 1
            logging.warning(f"Αποτυχία λήψης ticker '{symbol}' λόγω: {e}")
            logging.info(f"Επαναπροσπάθεια σε {2 ** retries} δευτερόλεπτα... (Προσπάθεια {retries}/{max_retries})")
            time.sleep(2 ** retries)  # Exponential backoff
    
    logging.error(f"Αποτυχία λήψης δεδομένων για το {symbol} μετά από {max_retries} προσπάθειες.")
    return None

def generate_forecast_plot(df: pd.DataFrame, symbol: str = "BTC-USD"):
    """
    Δημιουργεί ένα Plotly candlestick γράφημα για το δεδομένο DataFrame.
    Args:
        df (pd.DataFrame): DataFrame που περιέχει τα δεδομένα του κρυπτονομίσματος.
        symbol (str): Το σύμβολο του κρυπτονομίσματος.
    Returns:
        plotly.graph_objects.Figure: Ένα αντικείμενο Plotly figure.
    """
    logging.info("Δημιουργία γραφήματος")
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                        open=df['Open'],
                                        high=df['High'],
                                        low=df['Low'],
                                        close=df['Close'])])

    fig.update_layout(title=f"Ιστορικά Δεδομένα για {symbol}",
                      yaxis_title="Τιμή (USD)",
                      xaxis_title="Ημερομηνία",
                      xaxis_rangeslider_visible=True,
                      template="plotly_dark") # Χρησιμοποιούμε σκούρο θέμα για μοντέρνα εμφάνιση
    return fig

# Κύρια συνάρτηση για την εκτέλεση του script
def main():
    try:
        # Βήμα 1: Ανάκτηση δεδομένων
        data = get_crypto_data()
        if data is None:
            logging.error("Αποτυχία ανάκτησης δεδομένων. Έξοδος.")
            return

        # Βήμα 2: Δημιουργία γραφήματος
        plot_fig = generate_forecast_plot(data)

        # Βήμα 3: Αποθήκευση του γραφήματος ως HTML αρχείο
        plot_fig.write_html("index.html")
        logging.info("Το 'index.html' δημιουργήθηκε με επιτυχία.")

    except Exception as e:
        logging.error(f"Προέκυψε ένα σφάλμα: {e}")

if __name__ == "__main__":
    main()

