import os
import logging
from flask import Flask, render_template, request
from crypto_forecast import get_crypto_data, generate_forecast_plot
import datetime
from plotly.offline import plot
import plotly.graph_objects as go
import pandas as pd
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Starting Flask application...")

app = Flask(__name__, template_folder='templates')

# Check if required environment variables are set
if not os.environ.get("RENDER"):
    logging.warning("Not running on Render. Using a default port.")
    PORT = 8080
else:
    logging.info("Running on Render. Using PORT environment variable.")
    PORT = os.environ.get("PORT", 10000)

def create_error_plot(error_message):
    """
    Creates a simple Plotly figure with an error message.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=f"Error: {error_message}",
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=20, color="red")
    )
    fig.update_layout(
        title_text="Plot Generation Error",
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis_visible=False,
        yaxis_visible=False
    )
    return fig

@app.route('/', methods=['GET', 'POST'])
def index():
    logging.info("Request for the main page ('/'). Rendering index.html.")
    
    now = datetime.datetime.now()
    last_updated_time = now.strftime("%Y-%m-%d %H:%M:%S")

    selected_coin = request.form.get('coin_symbol', 'BTC-USD')
    plot_html = None
    error_message = None
    
    # Προσθήκη μικρής καθυστέρησης για να αποφευχθούν τα σφάλματα 'Too Many Requests'
    time.sleep(2)

    try:
        # Step 1: Get the data
        data = get_crypto_data(symbol=selected_coin)
        
        if data is None or data.empty:
            error_message = f"Δεν βρέθηκαν δεδομένα για το σύμβολο: {selected_coin}. Παρακαλώ δοκιμάστε ένα άλλο σύμβολο."
            logging.error(error_message)
            fig = create_error_plot(error_message)
            plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})
        else:
            # Step 2: Generate the plot
            fig = generate_forecast_plot(data, symbol=selected_coin)
            
            # Step 3: Convert the plot to HTML
            plot_html = plot(
                fig,
                output_type='div',
                include_plotlyjs=True,
                config={'displayModeBar': False}
            )
            logging.info("Η HTML του γραφήματος δημιουργήθηκε με επιτυχία.")

    except Exception as e:
        logging.error(f"Σφάλμα κατά τη δημιουργία του γραφήματος: {e}")
        error_message = str(e)
        fig = create_error_plot(error_message)
        plot_html = plot(fig, output_type='div', include_plotlyjs=True, config={'displayModeBar': False})


    return render_template(
        'index.html',
        plot_html=plot_html,
        last_updated=last_updated_time,
        current_coin=selected_coin,
        error=error_message
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
