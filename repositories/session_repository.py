"""Data access for the sessions table."""
from repositories.database import get_connection, row_to_dict


def create_session(course_id, started_at):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO sessions (course_id, started_at, status) VALUES (?, ?, 'active')",
            (course_id, started_at),
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


def list_active_sessions_by_instructor(instructor_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT s.*, c.code AS course_code, c.title AS course_title "
            "FROM sessions s JOIN courses c ON c.id = s.course_id "
            "WHERE c.instructor_id = ? AND s.status = 'active' ORDER BY s.started_at DESC",
            (instructor_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_sessions_by_course(course_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM sessions WHERE course_id = ? ORDER BY started_at DESC", (course_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def close_session(session_id, ended_at):
    """Close an active session; return True if a row was updated."""
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE sessions SET status = 'closed', ended_at = ? WHERE id = ? AND status = 'active'",
            (ended_at, session_id),
        )
        return cursor.rowcount == 1


def delete_session(session_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount
