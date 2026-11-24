"""Instructor login and logout."""
from functools import wraps

from flask import Blueprint, g, redirect, render_template, request, session, url_for

from routes.errors import is_api_request, json_error
from services import auth_service
from services.errors import AuthenticationError

auth_bp = Blueprint("auth", __name__)

SESSION_USER_KEY = "instructor_id"


def instructor_required(view):
    """Load the logged-in instructor into g.instructor or reject the request."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user_id = session.get(SESSION_USER_KEY)
        instructor = auth_service.get_instructor(user_id) if user_id is not None else None
        if instructor is None:
            session.pop(SESSION_USER_KEY, None)
            if is_api_request():
                return json_error("authentication_required", "Instructor login required.", 401)
            return redirect(url_for("auth.login"))
        g.instructor = instructor
        return view(*args, **kwargs)

    return wrapper


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get(SESSION_USER_KEY) is not None:
            return redirect(url_for("instructor.dashboard"))
        return render_template("login.html")

    institution_id = request.form.get("institution_id", "")
    try:
        instructor = auth_service.authenticate_instructor(
            institution_id, request.form.get("password", "")
        )
    except AuthenticationError as error:
        return render_template("login.html", error=error.message, institution_id=institution_id), 401

    session.clear()
    session[SESSION_USER_KEY] = instructor["id"]
    return redirect(url_for("instructor.dashboard"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
