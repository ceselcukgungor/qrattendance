"""Data access for the courses and course_enrollments tables."""
import time

from repositories.database import get_connection, row_to_dict


def create_course(code, title, instructor_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO courses (code, title, instructor_id, created_at) VALUES (?, ?, ?, ?)",
            (code, title, instructor_id, time.time()),
        )
        return cursor.lastrowid


def get_course_by_id(course_id):
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
        return row_to_dict(row)


def list_courses_by_instructor(instructor_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM courses WHERE instructor_id = ? ORDER BY code", (instructor_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def enroll_student(course_id, student_id):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO course_enrollments (course_id, student_id, enrolled_at) VALUES (?, ?, ?)",
            (course_id, student_id, time.time()),
        )


def is_student_enrolled(course_id, student_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM course_enrollments WHERE course_id = ? AND student_id = ?",
            (course_id, student_id),
        ).fetchone()
        return row is not None


def list_courses_by_student(student_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT c.* FROM courses c "
            "JOIN course_enrollments e ON e.course_id = c.id "
            "WHERE e.student_id = ? ORDER BY c.code",
            (student_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_enrolled_students(course_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT u.id, u.institution_id, u.full_name, u.email FROM users u "
            "JOIN course_enrollments e ON e.student_id = u.id "
            "WHERE e.course_id = ? ORDER BY u.full_name",
            (course_id,),
        ).fetchall()
        return [dict(row) for row in rows]
