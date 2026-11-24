"""Translation of service exceptions into HTTP responses."""
from flask import jsonify, render_template, request

from services.errors import (
    AuthenticationError,
    DuplicateAttendanceError,
    InvalidTokenError,
    NotEnrolledError,
    NotFoundError,
    PermissionDeniedError,
    ProxyDeviceError,
    ServiceError,
    SessionClosedError,
    TokenExpiredError,
    ValidationError,
)

STATUS_BY_ERROR = {
    ValidationError: 400,
    NotEnrolledError: 400,
    DuplicateAttendanceError: 400,
    AuthenticationError: 401,
    InvalidTokenError: 403,
    TokenExpiredError: 403,
    SessionClosedError: 403,
    ProxyDeviceError: 403,
    PermissionDeniedError: 403,
    NotFoundError: 404,
}


def status_for(error):
    for error_type in type(error).__mro__:
        if error_type in STATUS_BY_ERROR:
            return STATUS_BY_ERROR[error_type]
    return 400


def json_error(code, message, status):
    return jsonify({"error": code, "message": message}), status


def service_error_response(error):
    return json_error(error.code, error.message, status_for(error))


def is_api_request():
    return request.path.startswith("/api/")


def register_error_handlers(app):
    @app.errorhandler(ServiceError)
    def handle_service_error(error):
        if is_api_request():
            return service_error_response(error)
        return render_template("error.html", message=error.message), status_for(error)
