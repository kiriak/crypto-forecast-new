from flask import Flask, render_template_string
import pandas as pd
import numpy as np
import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Crypto Forecast Dashboard</title>
</head>
<body>
    <h2>Crypto Forecast for Next 6 Months</h2>
    <table border="1">
        <tr><th>Date</th><th>BTC (fake)</th><th>ETH (fake)</th></tr>
        {% for d, b, e in data %}
        <tr>
            <td>{{ d }}</td>
            <td>{{ b }}</td>
            <td>{{ e }}</td>
        </tr>
        {% endfor %}
    </table>
    <p style="color:gray">Demo data - για δοκιμή του dashboard!</p>
</body>
</html>
"""

@app.route("/")
def index():
    today = datetime.date.today()
    dates = [today + datetime.timedelta(days=30*i) for i in range(7)]
    btc = np.round(np.linspace(60000, 75000, 7) + np.random.randn(7)*1000, 2)
    eth = np.round(np.linspace(3000, 4500, 7) + np.random.randn(7)*100, 2)
    data = list(zip([str(d) for d in dates], btc, eth))
    return render_template_string(HTML, data=data)

if __name__ == "__main__":
    app.run(debug=True)
