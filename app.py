import os
from web_dashboard import app

if __name__ == '__main__':
    PORT = os.environ.get("PORT", 5000)
    app.run(host='0.0.0.0', port=int(PORT))
