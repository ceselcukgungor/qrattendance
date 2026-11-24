"""Application entry point: builds the Flask app and wires the layers together."""
import os

from flask import Flask

from repositories.database import configure_database, init_db
from routes import register_blueprints

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATABASE_PATH = os.path.join(BASE_DIR, "qrattendance.db")


def create_app(database_path=None):
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = database_path or os.environ.get(
        "QRATTENDANCE_DB", DEFAULT_DATABASE_PATH
    )
    app.config["SECRET_KEY"] = os.environ.get("QRATTENDANCE_SECRET_KEY", "dev-secret-change-me")

    configure_database(app.config["DATABASE_PATH"])
    init_db()

    register_blueprints(app)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
