"""Data access for the users table."""
import time

from repositories.database import get_connection, row_to_dict

_PUBLIC_COLUMNS = "id, institution_id, full_name, email, role, created_at"


def create_user(institution_id, full_name, email, password_hash, role):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO users (institution_id, full_name, email, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (institution_id, full_name, email, password_hash, role, time.time()),
        )
        return cursor.lastrowid


def get_user_by_id(user_id):
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return row_to_dict(row)


def get_user_by_institution_id(institution_id):
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE institution_id = ?", (institution_id,)
        ).fetchone()
        return row_to_dict(row)


def get_credentials_by_institution_id(institution_id):
    """Return the full row including password_hash, for authentication only."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE institution_id = ?", (institution_id,)
        ).fetchone()
        return row_to_dict(row)


def list_users_by_role(role):
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE role = ? ORDER BY full_name", (role,)
        ).fetchall()
        return [dict(row) for row in rows]


def update_user(user_id, full_name, email):
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user_id)
        )
        return cursor.rowcount


def delete_user(user_id):
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount
