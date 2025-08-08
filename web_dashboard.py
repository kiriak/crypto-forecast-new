import os
import logging
from flask import Flask, render_template, request
from crypto_forecast import get_prediction_plot
import datetime

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
    
    # Get the current time for the "last updated" message
    now = datetime.datetime.now()
    last_updated_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Call the function to get the prediction plot as HTML
    # We pass a default coin if no form data is submitted yet.
    selected_coin = request.form.get('coin_symbol', 'BTC-USD')
    try:
        plot_html = get_prediction_plot(selected_coin)
        logging.info("Successfully generated prediction plot HTML.")
    except Exception as e:
        logging.error(f"Error generating plot: {e}")
        plot_html = None
        # You might want to render an error page here instead
        return render_template('error.html', error=str(e), last_updated=last_updated_time)

    return render_template(
        'index.html',
        plot_html=plot_html,
        last_updated=last_updated_time,
        current_coin=selected_coin
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
