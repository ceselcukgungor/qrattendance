"""Data access for the attendance_records table."""
import time

from repositories.database import get_connection


def create_record(session_id, student_id, token_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO attendance_records (session_id, student_id, token_id, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, student_id, token_id, time.time()),
        )
        return cursor.lastrowid


def has_attended(session_id, student_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM attendance_records WHERE session_id = ? AND student_id = ?",
            (session_id, student_id),
        ).fetchone()
        return row is not None


def list_records_by_session(session_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT a.id, a.recorded_at, u.id AS student_id, u.institution_id, u.full_name "
            "FROM attendance_records a JOIN users u ON u.id = a.student_id "
            "WHERE a.session_id = ? ORDER BY a.recorded_at",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]
