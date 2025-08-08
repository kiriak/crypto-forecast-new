import requests
import pandas as pd
import logging
from prophet import Prophet
import plotly.graph_objects as go
import time

# Ρυθμίσεις για την καταγραφή (logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_crypto_data(symbol: str = "BTC-USD", days: int = 365):
    """
    Ανακτά δεδομένα κρυπτονομισμάτων από την CoinGecko API με εκθετικό backoff για επαναλήψεις.

    Args:
        symbol (str): Το σύμβολο του κρυπτονομίσματος (π.χ. "BTC-USD").
        days (int): Ο αριθμός των ημερών για τα ιστορικά δεδομένα.

    Returns:
        pd.DataFrame: Ένα DataFrame με τα δεδομένα του κρυπτονομίσματος ή None αν η ανάκτηση αποτύχει.
    """
    # Χάρτης συμβόλων για την CoinGecko API
    symbol_map = {
        "BTC-USD": "bitcoin",
        "ETH-USD": "ethereum",
        "SOL-USD": "solana",
        "DOGE-USD": "dogecoin",
        "XRP-USD": "ripple",
        "LTC-USD": "litecoin"
    }

    # Ελέγχουμε αν το σύμβολο υπάρχει στον χάρτη
    coingecko_id = symbol_map.get(symbol)
    if not coingecko_id:
        logging.error(f"Μη υποστηριζόμενο σύμβολο: {symbol}")
        return None

    api_url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}/market_chart?vs_currency=usd&days={days}"
    
    logging.info(f"Ανάκτηση δεδομένων για το σύμβολο: {coingecko_id} από την CoinGecko API")
    max_retries = 5
    # Ξεκινάμε τον χρόνο αναμονής από 5 δευτερόλεπτα
    wait_time = 5
    
    for retries in range(max_retries):
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()  # Θα προκαλέσει σφάλμα για μη επιτυχημένες απαντήσεις (π.χ. 404, 500)
            data = response.json()
            
            prices = data.get("prices", [])
            if not prices:
                logging.error("Δεν βρέθηκαν δεδομένα τιμών στην απάντηση της API.")
                return None
            
            # Μετατροπή των δεδομένων σε DataFrame της Pandas
            df = pd.DataFrame(prices, columns=['Date', 'Close'])
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            df.set_index('Date', inplace=True)
            
            logging.info(f"Τα δεδομένα ανακτήθηκαν με επιτυχία για το {symbol}. Γραμμές: {len(df)}")
            return df
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Αποτυχία λήψης δεδομένων από την CoinGecko: {e}")
            if retries < max_retries - 1:
                logging.info(f"Επαναπροσπάθεια σε {wait_time} δευτερόλεπτα... (Προσπάθεια {retries + 1}/{max_retries})")
                time.sleep(wait_time)  # Στατική αναμονή για μεγαλύτερη καθυστέρηση
                wait_time *= 2  # Αυξάνουμε τον χρόνο αναμονής για την επόμενη φορά
            
    logging.error(f"Αποτυχία λήψης δεδομένων για το {symbol} μετά από {max_retries} προσπάθειες.")
    return None

def generate_forecast_plot(data: pd.DataFrame, symbol: str = "BTC-USD"):
    """
    Δημιουργεί ένα Plotly γράφημα με τα ιστορικά δεδομένα και μια μελλοντική πρόβλεψη.

    Args:
        data (pd.DataFrame): Τα ιστορικά δεδομένα του κρυπτονομίσματος.
        symbol (str): Το σύμβολο του κρυπτονομίσματος.

    Returns:
        plotly.graph_objects.Figure: Το αντικείμενο Plotly figure με το γράφημα.
    """
    if 'Close' not in data.columns:
        logging.error("Τα δεδομένα εισόδου δεν περιέχουν τη στήλη 'Close'.")
        fig = go.Figure()
        fig.add_annotation(
            text="Λανθασμένη μορφή δεδομένων. Λείπει η στήλη 'Close'.",
            xref="paper", yref="paper", showarrow=False
        )
        return fig

    # Προετοιμασία δεδομένων για το μοντέλο Prophet
    df = data.reset_index()[['Date', 'Close']]
    df.columns = ['ds', 'y']

    # Εκκίνηση και προσαρμογή του μοντέλου Prophet
    model = Prophet()
    model.fit(df)

    # Δημιουργία μελλοντικών προβλέψεων
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # Δημιουργία του Plotly figure
    fig = go.Figure()

    # Προσθήκη ιστορικών δεδομένων
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines',
        name='Ιστορική Τιμή',
        line=dict(color='royalblue')
    ))

    # Προσθήκη δεδομένων πρόβλεψης
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        mode='lines',
        name='Προβλεπόμενη Τιμή',
        line=dict(color='firebrick', dash='dash')
    ))

    # Προσθήκη διαστήματος αβεβαιότητας
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        mode='lines',
        name='Κάτω Όριο',
        line=dict(width=0),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        mode='lines',
        name='Άνω Όριο',
        fill='tonexty',
        fillcolor='rgba(255, 0, 0, 0.1)',
        line=dict(width=0),
        showlegend=False
    ))

    # Ενημέρωση του layout για αισθητική
    fig.update_layout(
        title=f'Πρόβλεψη Τιμής για {symbol}',
        xaxis_title='Ημερομηνία',
        yaxis_title='Τιμή (USD)',
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter", color="black"),
        hovermode="x unified",
        margin=dict(l=50, r=50, t=70, b=50),
        xaxis_rangeslider_visible=True,
    )

    return fig
