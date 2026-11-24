"""Instructor authentication."""
from werkzeug.security import check_password_hash

from repositories import user_repository
from services.errors import AuthenticationError

INSTRUCTOR_ROLE = "instructor"


def authenticate_instructor(institution_id, password):
    """Return the instructor's public profile, or raise AuthenticationError."""
    institution_id = (institution_id or "").strip()
    user = user_repository.get_credentials_by_institution_id(institution_id) if institution_id else None
    if (
        user is None
        or user["role"] != INSTRUCTOR_ROLE
        or not check_password_hash(user["password_hash"], password or "")
    ):
        raise AuthenticationError("Invalid instructor ID or password.")
    return user_repository.get_user_by_id(user["id"])


def get_instructor(user_id):
    user = user_repository.get_user_by_id(user_id)
    if user is None or user["role"] != INSTRUCTOR_ROLE:
        return None
    return user
