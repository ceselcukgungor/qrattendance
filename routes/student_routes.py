"""Student check-in page and API."""
from flask import Blueprint, current_app, jsonify, render_template, request

from routes.errors import service_error_response
from services import attendance_service
from services.errors import ServiceError

student_bp = Blueprint("student", __name__)

DEVICE_COOKIE_NAME = "device_token"
DEVICE_COOKIE_MAX_AGE = 365 * 24 * 60 * 60


@student_bp.route("/checkin")
def checkin_page():
    return render_template("student/checkin.html", token=request.args.get("token", ""))


@student_bp.route("/api/attendance/checkin", methods=["POST"])
def checkin():
    payload = request.get_json(silent=True) or {}
    device_token = request.cookies.get(DEVICE_COOKIE_NAME)
    is_new_device = not device_token
    if is_new_device:
        device_token = attendance_service.generate_device_token()

    try:
        record = attendance_service.check_in(
            str(payload.get("token") or ""),
            str(payload.get("student_id") or ""),
            device_token,
        )
        response = jsonify({
            "status": "checked_in",
            "message": f"Attendance recorded for {record['full_name']}.",
            "student_id": record["student_id"],
            "full_name": record["full_name"],
            "checked_in_at": record["checked_in_at"],
        })
        response.status_code = 200
    except ServiceError as error:
        response, status = service_error_response(error)
        response.status_code = status

    if is_new_device:
        response.set_cookie(
            DEVICE_COOKIE_NAME,
            device_token,
            max_age=DEVICE_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=current_app.config.get("SESSION_COOKIE_SECURE", False),
        )
    return response
