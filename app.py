from flask import Flask
from flask_cors import CORS

from background.resource_tick_service import get_tick_service
import atexit
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True
)

from player.routes import player_bp
app.register_blueprint(player_bp)

from auth.routes import auth_bp
app.register_blueprint(auth_bp)

from resources.routes import resources_bp
app.register_blueprint(resources_bp)

from settlements.routes import settlements_bp
app.register_blueprint(settlements_bp)

from research.routes import research
app.register_blueprint(research)

if __name__ == '__main__':
    print("🚀 Starting resource tick service...")
    tick_service = get_tick_service()
    tick_service.start(interval_seconds=60)  # Tick every 60 seconds for testing
    atexit.register(lambda: tick_service.stop())
    
    app.run(debug=True, host='0.0.0.0', port=4000, use_reloader=False)