"""
Simple Flask server for hosting the payment WebApp
Run this alongside your bot to serve the payment interface
"""

from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS
import os
import logging

app = Flask(__name__, template_folder='.')
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Serve the payment WebApp"""
    return send_from_directory('.', 'payment.html')

@app.route('/payment')
def payment():
    """Serve the payment page with parameters"""
    return send_from_directory('.', 'payment.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    port = int(os.getenv('WEBAPP_PORT', 8080))
    logger.info(f"Starting WebApp server on port {port}")
    logger.info(f"WebApp URL will be: http://localhost:{port}/payment")

    # For production, use a proper WSGI server like gunicorn
    # gunicorn -w 4 -b 0.0.0.0:8080 webapp.server:app
    app.run(host='0.0.0.0', port=port, debug=False)
