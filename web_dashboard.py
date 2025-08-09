import os
import logging
from flask import Flask, render_template, request, jsonify
import datetime
from plotly.offline import plot
import plotly.graph_objects as go
import pandas as pd
from prophet import Prophet
import json
import requests
import warnings
import time

# Παράκαμψη της FutureWarning από το Prophet
warnings.simplefilter(action='ignore', category=FutureWarning)

# Ρύθμιση της καταγραφής (logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Εκκίνηση της εφαρμογής Flask...")

app = Flask(__name__, template_folder='templates')

# Έλεγχος αν εκτελείται στο Render για τη σωστή θύρα
if not os.environ.get("RENDER"):
    logging.warning("Δεν εκτελείται στο Render. Χρήση προεπιλεγμένης θύρας.")
    PORT = 8080
else:
    logging.info("Εκτελείται στο Render. Χρήση της μεταβλητής περιβάλλοντος PORT.")
    PORT = os.environ.get("PORT", 10000)

# ==============================================================================
# ΠΡΟΣΟΧΗ: ΠΡΟΣΘΕΣΕ ΕΔΩ ΤΟ ΔΙΚΟ ΣΟΥ API KEY ΑΠΟ ΤΟ COINAPI
# Δημιούργησε ένα δωρεάν κλειδί στο https://www.coinapi.io
# ==============================================================================
API_KEY = 6ce7f7f2-f70b-4fb6-85ab-e3b215ec4444

def get_crypto_data(symbol='BTC', period_days='730'):
    """
    Ανακτά ιστορικά δεδομένα κρυπτονομισμάτων από το CoinAPI.
    """
    # Το CoinAPI απαιτεί το σύμβολο με μορφή 'ASSET_ID_EXCHANGE'. Χρησιμοποιούμε 'USD'
    # και το ανταλλακτήριο 'COINBASE' για σταθερότητα.
    # Επίσης, η ημερομηνία έναρξης υπολογίζεται από το period_days
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=int(period_days))
    
    url = f"https://rest.coinapi.io/v1/ohlcv/{symbol}/USD/history?period_id=1DAY&time_start={start_date.isoformat()}&time_end={end_date.isoformat()}"
    headers = {'X-CoinAPI-Key': API_KEY}

    retries = 3
    for i in range(retries):
        try:
            logging.info(f"Ανάκτηση δεδομένων για το σύμβολο: {symbol} από CoinAPI (Προσπάθεια {i+1}/{retries})...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logging.warning(f"Δεν βρέθηκαν δεδομένα για το σύμβολο {symbol} στην προσπάθεια {i+1}. Δοκιμάζω ξανά...")
                time.sleep(2)
                continue

            # Μετατροπή των δεδομένων σε DataFrame
            df = pd.DataFrame(data)
            df['time_close'] = pd.to_datetime(df['time_close'])
            df.rename(columns={'time_close': 'ds', 'price_close': 'y'}, inplace=True)
            return df
        except requests.exceptions.RequestException as e:
            logging.error(f"Σφάλμα κατά την ανάκτηση δεδομένων από το API στην προσπάθεια {i+1}: {e}")
            time.sleep(2)
        except Exception as e:
            logging.error(f"Γενικό σφάλμα κατά την επεξεργασία δεδομένων στην προσπάθεια {i+1}: {e}")
            time.sleep(2)
    
    logging.error("Αποτυχία ανάκτησης δεδομένων μετά από πολλαπλές προσπάθειες.")
    return pd.DataFrame()

def generate_forecast_plot(data, symbol='bitcoin', periods=180):
    """
    Δημιουργεί ένα γράφημα πρόβλεψης τιμών κρυπτονομισμάτων χρησιμοποιώντας το Prophet.
    """
    try:
        logging.info(f"Δημιουργία γραφήματος πρόβλεψης για το σύμβολο: {symbol}...")
        
        m = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        m.fit(data)

        future = m.make_future_dataframe(periods=periods)
        forecast = m.predict(future)

        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['ds'],
            y=data['y'],
            mode='lines',
            name='Ιστορικές Τιμές',
            line=dict(color='#008080')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat'],
            mode='lines',
            name='Πρόβλεψη',
            line=dict(color='#8A2BE2', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_upper'],
            mode='lines',
            name='Ανώτερο Όριο',
            line=dict(color='rgba(138, 43, 226, 0.2)', width=0),
            fill=None
        ))
        fig.add_trace(go.Scatter(
            x=forecast['ds'],
            y=forecast['yhat_lower'],
            mode='lines',
            name='Κατώτερο Όριο',
            fill='tonexty',
            fillcolor='rgba(138, 43, 226, 0.2)',
            line=dict(color='rgba(138, 43, 226, 0.2)', width=0)
        ))

        fig.update_layout(
            title=f'Πρόβλεψη Τιμής {symbol.capitalize()} για τους επόμενους {periods} ημέρες',
            xaxis_title='Ημερομηνία',
            yaxis_title='Τιμή (USD)',
            template='plotly_white',
            xaxis_rangeslider_visible=True,
            showlegend=True
        )
        return fig
    except Exception as e:
        logging.error(f"Σφάλμα κατά τη δημιουργία του γραφήματος πρόβλεψης: {e}")
        return create_error_plot(f"Σφάλμα: {e}")

def create_error_plot(error_message):
    """
    Δημιουργεί ένα απλό γράφημα Plotly με ένα μήνυμα σφάλματος.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=f"Σφάλμα: {error_message}",
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=20, color="red")
    )
    fig.update_layout(
        title_text="Σφάλμα Δημιουργίας Γραφήματος",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis_visible=False,
        yaxis_visible=False
    )
    return fig

@app.route('/', methods=['GET'])
def index():
    """
    Χειρίζεται την αρχική αίτηση για την κύρια σελίδα.
    Επιστρέφει το index.html.
    """
    logging.info("Αίτηση για την κύρια σελίδα ('/'). Επιστροφή index.html.")
    now = datetime.datetime.now()
    last_updated_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Αρχική δημιουργία γραφήματος για το bitcoin
    try:
        data = get_crypto_data(symbol='BTC')
        if data.empty:
            error_message = "Δεν ήταν δυνατή η λήψη δεδομένων για το Bitcoin. Παρακαλώ δοκιμάστε ένα άλλο νόμισμα."
            fig = create_error_plot(error_message)
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            current_coin = 'Error'
        else:
            fig = generate_forecast_plot(data, symbol='BTC')
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            current_coin = 'BTC'
    except Exception as e:
        logging.error(f"Σφάλμα στην αρχική δημιουργία γραφήματος: {e}")
        fig = create_error_plot(str(e))
        plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
        current_coin = 'Error'

    return render_template(
        'index.html',
        plot_html=plot_html,
        last_updated=last_updated_time,
        current_coin=current_coin
    )

@app.route('/forecast', methods=['POST'])
def forecast():
    """
    Χειρίζεται την αίτηση POST για τη δημιουργία νέας πρόβλεψης.
    Επιστρέφει το HTML του γραφήματος ως JSON.
    """
    logging.info("Ελήφθη αίτηση για νέα πρόβλεψη.")
    
    selected_coin = request.json.get('coin_symbol', 'BTC')
    logging.info(f"Δημιουργία πρόβλεψης για: {selected_coin}")

    try:
        data = get_crypto_data(symbol=selected_coin)
        
        if data is None or data.empty:
            error_message = f"Δεν βρέθηκαν δεδομένα για το σύμβολο: {selected_coin}. Παρακαλώ δοκιμάστε ένα άλλο σύμβολο."
            logging.error(error_message)
            fig = create_error_plot(error_message)
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
            return jsonify({'plot_html': plot_html, 'error': error_message})
        else:
            fig = generate_forecast_plot(data, symbol=selected_coin)
            plot_html = plot(
                fig,
                output_type='div',
                include_plotlyjs=True,
                config={'displayModeBar': False}
            )
            logging.info("Η HTML του γραφήματος δημιουργήθηκε με επιτυχία.")
            return jsonify({'plot_html': plot_html, 'error': None})

    except Exception as e:
        logging.error(f"Σφάλμα κατά τη δημιουργία του γραφήματος: {e}")
        error_message = str(e)
        fig = create_error_plot(error_message)
        plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
        return jsonify({'plot_html': plot_html, 'error': error_message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
