"""Check-in validation, attendance statistics, and roster export."""
import csv
import io
import time

from repositories import (
    attendance_repository,
    course_repository,
    qr_token_repository,
    user_repository,
)
from repositories.database import DuplicateRecordError
from services import qr_service, session_service
from services.errors import (
    DuplicateAttendanceError,
    InvalidTokenError,
    NotEnrolledError,
    ProxyDeviceError,
    SessionClosedError,
    TokenExpiredError,
    ValidationError,
)

MAX_DEVICE_TOKEN_LENGTH = 128


def _clean(value, field, max_length=None):
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field} is required.")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field} is too long.")
    return value


def check_in(token, student_id, device_token):
    """Record attendance for a student.

    `student_id` is the institutional student ID (e.g. "STU-2001"). Checks run in order:
    token exists, token within TTL, session active, student enrolled, no duplicate
    student, no device reuse for another student.
    """
    token = _clean(token, "Token")
    student_id = _clean(student_id, "Student ID")
    device_token = _clean(device_token, "Device token", MAX_DEVICE_TOKEN_LENGTH)

    now = time.time()
    token_row = qr_token_repository.get_token(token)
    if token_row is None:
        raise InvalidTokenError("Invalid QR code.")
    if not qr_service.is_token_fresh(token_row["created_at"], now):
        raise TokenExpiredError("This QR code has expired. Scan the current code.")

    session = session_service.get_session(token_row["session_id"])
    if session["status"] != "active":
        raise SessionClosedError("This attendance session is closed.")

    student = user_repository.get_user_by_institution_id(student_id)
    if (
        student is None
        or student["role"] != "student"
        or not course_repository.is_student_enrolled(session["course_id"], student["id"])
    ):
        raise NotEnrolledError("This student is not enrolled in the course.")

    _ensure_unique(session["id"], student["id"], device_token)

    try:
        record_id = attendance_repository.create_record(
            session["id"], student["id"], token_row["id"], device_token, now
        )
    except DuplicateRecordError:
        # A concurrent request won the race; report the matching rule.
        _ensure_unique(session["id"], student["id"], device_token)
        raise DuplicateAttendanceError("Attendance is already recorded.") from None

    return {
        "id": record_id,
        "session_id": session["id"],
        "student_id": student["institution_id"],
        "full_name": student["full_name"],
        "checked_in_at": now,
    }


def _ensure_unique(session_id, student_pk, device_token):
    if attendance_repository.get_record(session_id, student_pk) is not None:
        raise DuplicateAttendanceError("Attendance is already recorded for this student.")
    device_record = attendance_repository.get_record_by_device(session_id, device_token)
    if device_record is not None:
        raise ProxyDeviceError(
            "This device has already been used to check in another student."
        )


def get_session_stats(session_id):
    session = session_service.get_session(session_id)
    enrolled = course_repository.count_enrolled_students(session["course_id"])
    attended = attendance_repository.count_records_by_session(session_id)
    absent = max(enrolled - attended, 0)
    attendance_rate = round(attended / enrolled * 100, 1) if enrolled else 0.0
    absence_rate = round(absent / enrolled * 100, 1) if enrolled else 0.0
    return {
        "session_id": session_id,
        "status": session["status"],
        "attended": attended,
        "enrolled": enrolled,
        "absent": absent,
        "attendance_rate": attendance_rate,
        "absence_rate": absence_rate,
    }


def _format_timestamp(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def export_roster_csv(session_id):
    """Return the full roster for a session (present and absent students) as CSV text."""
    session = session_service.get_session(session_id)
    students = course_repository.list_enrolled_students(session["course_id"])
    records = {
        record["student_id"]: record
        for record in attendance_repository.list_records_by_session(session_id)
    }

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["student_id", "full_name", "email", "status", "checked_in_at"])
    for student in students:
        record = records.get(student["id"])
        writer.writerow([
            student["institution_id"],
            student["full_name"],
            student["email"],
            "present" if record else "absent",
            _format_timestamp(record["checked_in_at"]) if record else "",
        ])
    return buffer.getvalue()
