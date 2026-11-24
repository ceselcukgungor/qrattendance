"""Presentation layer. Routes depend on services only."""
from routes.auth_routes import auth_bp
from routes.errors import register_error_handlers
from routes.instructor_routes import instructor_bp
from routes.main_routes import main_bp
from routes.student_routes import student_bp


def register_blueprints(app):
    for blueprint in (main_bp, auth_bp, instructor_bp, student_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)
