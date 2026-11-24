"""Instructor pages and session management API."""
from flask import Blueprint, Response, current_app, g, jsonify, render_template, request

from routes.auth_routes import instructor_required
from services import attendance_service, course_service, qr_service, session_service
from services.errors import SessionClosedError, ValidationError

instructor_bp = Blueprint("instructor", __name__)


@instructor_bp.route("/instructor")
@instructor_required
def dashboard():
    courses = course_service.list_instructor_courses(g.instructor["id"])
    return render_template("instructor/dashboard.html", instructor=g.instructor, courses=courses)


@instructor_bp.route("/instructor/sessions/<int:session_id>")
@instructor_required
def session_page(session_id):
    attendance_session = session_service.get_owned_session(g.instructor["id"], session_id)
    return render_template(
        "instructor/session.html",
        instructor=g.instructor,
        attendance_session=attendance_session,
        refresh_seconds=current_app.config["QR_REFRESH_SECONDS"],
    )


@instructor_bp.route("/api/sessions/start", methods=["POST"])
@instructor_required
def start_session():
    payload = request.get_json(silent=True) or {}
    course_id = payload.get("course_id")
    if isinstance(course_id, str) and course_id.isdigit():
        course_id = int(course_id)
    if not isinstance(course_id, int) or isinstance(course_id, bool):
        raise ValidationError("course_id must be an integer.")

    attendance_session = session_service.start_session(g.instructor["id"], course_id)
    return jsonify({
        "session_id": attendance_session["id"],
        "course_id": attendance_session["course_id"],
        "status": attendance_session["status"],
        "started_at": attendance_session["started_at"],
    }), 201


@instructor_bp.route("/api/sessions/<int:session_id>/end", methods=["POST"])
@instructor_required
def end_session(session_id):
    attendance_session = session_service.close_session(g.instructor["id"], session_id)
    return jsonify({
        "session_id": attendance_session["id"],
        "status": attendance_session["status"],
        "ended_at": attendance_session["ended_at"],
        "stats": attendance_service.get_session_stats(session_id),
    }), 200


@instructor_bp.route("/api/sessions/<int:session_id>/qr")
@instructor_required
def session_qr(session_id):
    attendance_session = session_service.get_owned_session(g.instructor["id"], session_id)

    qr_payload = None
    if attendance_session["status"] == "active":
        try:
            qr_payload = qr_service.issue_token(
                session_id,
                current_app.config["SERVER_PORT"],
                current_app.config.get("CHECKIN_HOST"),
            )
        except SessionClosedError:
            qr_payload = None

    stats = attendance_service.get_session_stats(session_id)
    return jsonify({
        "session_id": session_id,
        "session_status": stats["status"],
        "qr_image": qr_payload["qr_image"] if qr_payload else None,
        "checkin_url": qr_payload["checkin_url"] if qr_payload else None,
        "token_created_at": qr_payload["created_at"] if qr_payload else None,
        "ttl_seconds": qr_service.TOKEN_TTL_SECONDS,
        "present_count": stats["attended"],
        "total_enrolled": stats["enrolled"],
        "absent_count": stats["absent"],
        "attendance_rate": stats["attendance_rate"],
        "absenteeism_rate": stats["absence_rate"],
    })


@instructor_bp.route("/api/sessions/<int:session_id>/attendance")
@instructor_required
def session_attendance(session_id):
    session_service.get_owned_session(g.instructor["id"], session_id)
    stats = attendance_service.get_session_stats(session_id)
    return jsonify({
        "session_id": session_id,
        "session_status": stats["status"],
        "students": attendance_service.list_checked_in_students(session_id),
        "present_count": stats["attended"],
        "total_enrolled": stats["enrolled"],
        "absent_count": stats["absent"],
        "attendance_rate": stats["attendance_rate"],
        "absenteeism_rate": stats["absence_rate"],
    })


@instructor_bp.route("/api/sessions/<int:session_id>/export")
@instructor_required
def export_session(session_id):
    attendance_session = session_service.get_owned_session(g.instructor["id"], session_id)
    filename = f"attendance_{attendance_session['course_code']}_session_{session_id}.csv"
    return Response(
        attendance_service.export_roster_csv(session_id),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
