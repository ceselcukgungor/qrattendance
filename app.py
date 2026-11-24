"""Application factory and development server entry point."""
import os
import secrets

from flask import Flask

from repositories.database import configure_database, init_db
from routes import register_blueprints
from services.qr_service import get_lan_ip

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATABASE_PATH = os.path.join(BASE_DIR, "qrattendance.db")
HOST = "0.0.0.0"
PORT = 5000


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("QRATTENDANCE_SECRET_KEY") or secrets.token_hex(32),
        DATABASE_PATH=os.environ.get("QRATTENDANCE_DB", DEFAULT_DATABASE_PATH),
        SERVER_PORT=PORT,
        CHECKIN_HOST=os.environ.get("QRATTENDANCE_CHECKIN_HOST"),
        QR_REFRESH_SECONDS=5,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config_overrides:
        app.config.update(config_overrides)

    configure_database(app.config["DATABASE_PATH"])
    init_db()

    register_blueprints(app)
    return app


if __name__ == "__main__":
    application = create_app()
    print(f"Check-in server reachable on the LAN at http://{get_lan_ip()}:{PORT}")
    application.run(host=HOST, port=PORT, debug=os.environ.get("FLASK_DEBUG") == "1")
