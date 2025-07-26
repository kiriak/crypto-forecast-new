    # web_dashboard.py - Εξαιρετικά απλή δοκιμή

    from flask import Flask
    import logging

    # Configure logging for the Flask application
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        """
        The main route of the application. Returns a simple "Hello, World!" message.
        """
        logging.info("Request for the main page ('/'). Returning 'Hello, World!'.")
        return "Hello, World! Η εφαρμογή Flask λειτουργεί!"

    @app.route('/health')
    def health_check():
        """
        Health check for Render.com
        """
        return "OK", 200

    if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0', port=5000)
    