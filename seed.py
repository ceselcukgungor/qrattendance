"""Populate the local database with test data that simulates an institutional integration.

Usage:  python seed.py
WARNING: drops and recreates all tables in the configured database.

All seeded accounts share the development-only password below.
"""
from werkzeug.security import generate_password_hash

from app import DEFAULT_DATABASE_PATH
from repositories import course_repository, user_repository
from repositories.database import configure_database, reset_db

DEV_PASSWORD = "password123"

INSTRUCTORS = [
    ("INS-1001", "Dr. Alice Morgan", "alice.morgan@university.test"),
    ("INS-1002", "Prof. Brian Chen", "brian.chen@university.test"),
]

STUDENTS = [
    ("STU-2001", "Emma Wilson", "emma.wilson@university.test"),
    ("STU-2002", "Liam Johnson", "liam.johnson@university.test"),
    ("STU-2003", "Olivia Brown", "olivia.brown@university.test"),
    ("STU-2004", "Noah Davis", "noah.davis@university.test"),
    ("STU-2005", "Ava Martinez", "ava.martinez@university.test"),
    ("STU-2006", "Ethan Garcia", "ethan.garcia@university.test"),
]

# (course code, title, instructor institution ID, enrolled student institution IDs)
COURSES = [
    ("CS101", "Introduction to Programming", "INS-1001",
     ["STU-2001", "STU-2002", "STU-2003", "STU-2004"]),
    ("CS205", "Database Systems", "INS-1001",
     ["STU-2003", "STU-2004", "STU-2005"]),
    ("MATH150", "Discrete Mathematics", "INS-1002",
     ["STU-2001", "STU-2005", "STU-2006"]),
]


def seed():
    configure_database(DEFAULT_DATABASE_PATH)
    reset_db()

    password_hash = generate_password_hash(DEV_PASSWORD)
    user_ids = {}

    for institution_id, full_name, email in INSTRUCTORS:
        user_ids[institution_id] = user_repository.create_user(
            institution_id, full_name, email, password_hash, "instructor"
        )
    for institution_id, full_name, email in STUDENTS:
        user_ids[institution_id] = user_repository.create_user(
            institution_id, full_name, email, password_hash, "student"
        )

    enrollment_count = 0
    for code, title, instructor_key, student_keys in COURSES:
        course_id = course_repository.create_course(code, title, user_ids[instructor_key])
        for student_key in student_keys:
            course_repository.enroll_student(course_id, user_ids[student_key])
            enrollment_count += 1

    print(f"Database seeded at {DEFAULT_DATABASE_PATH}")
    print(f"  Instructors: {len(INSTRUCTORS)}")
    print(f"  Students:    {len(STUDENTS)}")
    print(f"  Courses:     {len(COURSES)}")
    print(f"  Enrollments: {enrollment_count}")


if __name__ == "__main__":
    seed()
