"""Course queries for the instructor dashboard."""
from repositories import course_repository, session_repository


def list_instructor_courses(instructor_id):
    """Return the instructor's courses with enrollment counts and any active session id."""
    courses = []
    for course in course_repository.list_courses_by_instructor(instructor_id):
        active = session_repository.get_active_session_for_course(course["id"])
        courses.append({
            "id": course["id"],
            "code": course["code"],
            "title": course["title"],
            "enrolled": course_repository.count_enrolled_students(course["id"]),
            "active_session_id": active["id"] if active else None,
        })
    return courses
