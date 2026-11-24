"""Attendance session lifecycle."""
import time

from repositories import course_repository, session_repository
from services.errors import NotFoundError, PermissionDeniedError, SessionClosedError


def get_session(session_id):
    session = session_repository.get_session_by_id(session_id)
    if session is None:
        raise NotFoundError("Session not found.")
    return session


def require_active_session(session_id):
    session = get_session(session_id)
    if session["status"] != "active":
        raise SessionClosedError("This attendance session is closed.")
    return session


def _require_owned_course(instructor_id, course_id):
    course = course_repository.get_course_by_id(course_id)
    if course is None:
        raise NotFoundError("Course not found.")
    if course["instructor_id"] != instructor_id:
        raise PermissionDeniedError("You are not the instructor of this course.")
    return course


def start_session(instructor_id, course_id):
    """Start a session for the course, or return the one already active."""
    _require_owned_course(instructor_id, course_id)
    active = session_repository.get_active_session_for_course(course_id)
    if active is not None:
        return active
    session_id = session_repository.create_session(course_id, time.time())
    return session_repository.get_session_by_id(session_id)


def close_session(instructor_id, session_id):
    session = get_session(session_id)
    _require_owned_course(instructor_id, session["course_id"])
    if not session_repository.close_session(session_id, time.time()):
        raise SessionClosedError("This attendance session is already closed.")
    return session_repository.get_session_by_id(session_id)


def list_active_sessions(instructor_id):
    return session_repository.list_active_sessions_by_instructor(instructor_id)
