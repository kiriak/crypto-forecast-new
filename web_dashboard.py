import os
import logging
from flask import Flask, render_template, request
from crypto_forecast import get_crypto_data, generate_forecast_plot # Ενημερωμένη εισαγωγή
import datetime
from plotly.offline import plot # Χρειάζεται να εισάγουμε και το plot

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting Flask application...")

app = Flask(__name__, template_folder='templates')

# Check if required environment variables are set
if not os.environ.get("RENDER"):
    logging.warning("Not running on Render. Using a default port.")
    PORT = 8080
else:
    logging.info("Running on Render. Using PORT environment variable.")
    PORT = os.environ.get("PORT", 10000)

@app.route('/', methods=['GET', 'POST'])
def index():
    logging.info("Request for the main page ('/'). Rendering index.html.")
    
    now = datetime.datetime.now()
    last_updated_time = now.strftime("%Y-%m-%d %H:%M:%S")

    selected_coin = request.form.get('coin_symbol', 'BTC-USD')
    plot_html = None
    error_message = None

    try:
        # Step 1: Get the data
        data = get_crypto_data(symbol=selected_coin)
        
        if data is None or data.empty:
            error_message = f"No data found for the symbol: {selected_coin}."
            logging.error(error_message)
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
            logging.info("Successfully generated prediction plot HTML.")

    except Exception as e:
        logging.error(f"Error generating plot: {e}")
        error_message = str(e)

    return render_template(
        'index.html',
        plot_html=plot_html,
        last_updated=last_updated_time,
        current_coin=selected_coin,
        error=error_message
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
