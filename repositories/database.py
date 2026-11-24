"""SQLite connection management. The only module that opens database connections."""
import os
import sqlite3
from contextlib import contextmanager

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

# Tables in dependency order (parents first); used for resets.
TABLES = ("users", "courses", "course_enrollments", "sessions", "qr_tokens", "attendance_records")

_database_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qrattendance.db"
)


def configure_database(path):
    global _database_path
    _database_path = path


def get_database_path():
    return _database_path


def _connect():
    connection = sqlite3.connect(_database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    # WAL allows concurrent readers while a writer is active.
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
    return connection


@contextmanager
def get_connection():
    """Yield a connection; commit on success, roll back on error, always close."""
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        schema = schema_file.read()
    with get_connection() as connection:
        connection.executescript(schema)


def reset_db():
    """Drop all tables and recreate the schema. Intended for seeding and tests."""
    with get_connection() as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        for table in reversed(TABLES):
            connection.execute(f"DROP TABLE IF EXISTS {table}")
    init_db()


def row_to_dict(row):
    return dict(row) if row is not None else None
