"""Data access for the sessions table (class meetings)."""
import time

from repositories.database import get_connection, row_to_dict


def create_session(course_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO sessions (course_id, started_at, status) VALUES (?, ?, 'active')",
            (course_id, time.time()),
        )
        return cursor.lastrowid


def get_session_by_id(session_id):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return row_to_dict(row)


def get_active_session_for_course(course_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM sessions WHERE course_id = ? AND status = 'active' "
            "ORDER BY started_at DESC LIMIT 1",
            (course_id,),
        ).fetchone()
        return row_to_dict(row)


def close_session(session_id):
    with get_connection() as connection:
        connection.execute(
            "UPDATE sessions SET status = 'closed', ended_at = ? WHERE id = ? AND status = 'active'",
            (time.time(), session_id),
        )


def list_sessions_by_course(course_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM sessions WHERE course_id = ? ORDER BY started_at DESC", (course_id,)
        ).fetchall()
        return [dict(row) for row in rows]
