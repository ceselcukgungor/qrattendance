"""Domain exceptions raised by the service layer."""


class ServiceError(Exception):
    """Base class for business rule violations; `code` is a stable machine-readable identifier."""

    code = "service_error"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class AuthenticationError(ServiceError):
    code = "authentication_failed"


class NotFoundError(ServiceError):
    code = "not_found"


class PermissionDeniedError(ServiceError):
    code = "permission_denied"


class ValidationError(ServiceError):
    code = "validation_error"


class SessionClosedError(ServiceError):
    code = "session_closed"


class InvalidTokenError(ServiceError):
    code = "invalid_token"


class TokenExpiredError(ServiceError):
    code = "token_expired"


class NotEnrolledError(ServiceError):
    code = "not_enrolled"


class DuplicateAttendanceError(ServiceError):
    code = "duplicate_attendance"


class ProxyDeviceError(ServiceError):
    code = "proxy_device"
