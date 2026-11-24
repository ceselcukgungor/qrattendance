"""Data access for the qr_tokens table."""
from repositories.database import get_connection, row_to_dict


def create_token(session_id, token, created_at):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO qr_tokens (session_id, token, created_at) VALUES (?, ?, ?)",
            (session_id, token, created_at),
        )
        return cursor.lastrowid


def get_token(token):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM qr_tokens WHERE token = ?", (token,)).fetchone()
        return row_to_dict(row)


def get_latest_token_for_session(session_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM qr_tokens WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,),
        ).fetchone()
        return row_to_dict(row)


def delete_tokens_created_before(cutoff):
    """Delete tokens older than cutoff; attendance records keep a NULL token_id."""
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM qr_tokens WHERE created_at < ?", (cutoff,))
        return cursor.rowcount


def delete_tokens_for_session(session_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM qr_tokens WHERE session_id = ?", (session_id,))
        return cursor.rowcount
