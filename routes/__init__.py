"""Presentation layer: Flask blueprints. Routes call services only, never repositories."""
from routes.main_routes import main_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
