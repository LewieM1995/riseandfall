from flask import Flask
from flask_cors import CORS

from systems.resources.resource_tick_service import get_tick_service
import atexit
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True
)

from routes.army import army_bp
app.register_blueprint(army_bp)

from routes.resources import resource_bp
app.register_blueprint(resource_bp)

from routes.signup import sign_up_bp
app.register_blueprint(sign_up_bp)

from routes.login import login_bp
app.register_blueprint(login_bp)

if __name__ == '__main__':
    print("🚀 Starting resource tick service...")
    tick_service = get_tick_service()
    tick_service.start(interval_seconds=60)  # Tick every 60 seconds for testing
    atexit.register(lambda: tick_service.stop())
    
    app.run(debug=True, host='0.0.0.0', port=4000, use_reloader=False)