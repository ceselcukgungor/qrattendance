"""Data access for the attendance_records table."""
import sqlite3

from repositories.database import DuplicateRecordError, get_connection, row_to_dict


def create_record(session_id, student_id, token_id, device_token, checked_in_at):
    """Insert a record; raise DuplicateRecordError if student or device already checked in."""
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO attendance_records "
                "(session_id, student_id, token_id, device_token, checked_in_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, student_id, token_id, device_token, checked_in_at),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError as error:
        if "UNIQUE" in str(error):
            raise DuplicateRecordError(str(error)) from error
        raise


def get_record(session_id, student_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM attendance_records WHERE session_id = ? AND student_id = ?",
            (session_id, student_id),
        ).fetchone()
        return row_to_dict(row)


def get_record_by_device(session_id, device_token):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM attendance_records WHERE session_id = ? AND device_token = ?",
            (session_id, device_token),
        ).fetchone()
        return row_to_dict(row)


def count_records_by_session(session_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM attendance_records WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row[0]


def list_records_by_session(session_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT a.id, a.checked_in_at, a.device_token, u.id AS student_id, "
            "u.institution_id, u.full_name, u.email "
            "FROM attendance_records a JOIN users u ON u.id = a.student_id "
            "WHERE a.session_id = ? ORDER BY a.checked_in_at",
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_record(record_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM attendance_records WHERE id = ?", (record_id,))
        return cursor.rowcount
