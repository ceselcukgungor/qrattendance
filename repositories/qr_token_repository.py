"""Data access for the qr_tokens table. TTL rules are enforced in the service layer."""
from repositories.database import get_connection, row_to_dict


def create_token(session_id, token, issued_at, expires_at):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO qr_tokens (session_id, token, issued_at, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, token, issued_at, expires_at),
        )
        return cursor.lastrowid


def get_token(token):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM qr_tokens WHERE token = ?", (token,)).fetchone()
        return row_to_dict(row)


def delete_expired_tokens(now):
    """Remove expired tokens that no attendance record references."""
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM qr_tokens WHERE expires_at < ? "
            "AND id NOT IN (SELECT token_id FROM attendance_records WHERE token_id IS NOT NULL)",
            (now,),
        )
        return cursor.rowcount
