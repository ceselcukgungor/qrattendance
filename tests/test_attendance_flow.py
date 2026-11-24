"""End-to-end tests for token issuance and check-in rules against a temporary database."""
import os
import tempfile
import time
import unittest

from repositories import course_repository, qr_token_repository, user_repository
from repositories.database import configure_database, reset_db
from services import attendance_service, qr_service, session_service
from services.errors import (
    DuplicateAttendanceError,
    InvalidTokenError,
    NotEnrolledError,
    PermissionDeniedError,
    ProxyDeviceError,
    SessionClosedError,
    TokenExpiredError,
)

PORT = 5000


class AttendanceFlowTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        configure_database(os.path.join(self._tmp.name, "test.db"))
        reset_db()

        self.instructor_id = user_repository.create_user(
            "INS-1", "Test Instructor", "ins@example.test", "x", "instructor"
        )
        self.other_instructor_id = user_repository.create_user(
            "INS-2", "Other Instructor", "ins2@example.test", "x", "instructor"
        )
        self.course_id = course_repository.create_course("CS101", "Programming", self.instructor_id)
        for number in (1, 2, 3):
            student_pk = user_repository.create_user(
                f"STU-{number}", f"Student {number}", f"s{number}@example.test", "x", "student"
            )
            course_repository.enroll_student(self.course_id, student_pk)
        user_repository.create_user("STU-9", "Outsider", "s9@example.test", "x", "student")

        self.session = session_service.start_session(self.instructor_id, self.course_id)

    def tearDown(self):
        self._tmp.cleanup()

    def _issue(self):
        return qr_service.issue_token(self.session["id"], PORT)["token"]

    def test_issue_token_payload(self):
        payload = qr_service.issue_token(self.session["id"], PORT)
        self.assertIn(f"token={payload['token']}", payload["checkin_url"])
        self.assertTrue(payload["qr_image"].startswith("data:image/png;base64,"))
        self.assertEqual(payload["ttl_seconds"], 45.0)

    def test_valid_check_in_succeeds(self):
        record = attendance_service.check_in(self._issue(), "STU-1", "device-a")
        self.assertEqual(record["student_id"], "STU-1")
        stats = attendance_service.get_session_stats(self.session["id"])
        self.assertEqual((stats["attended"], stats["enrolled"], stats["absent"]), (1, 3, 2))
        self.assertEqual(stats["attendance_rate"], 33.3)
        self.assertEqual(stats["absence_rate"], 66.7)

    def test_expired_token_rejected(self):
        token = qr_service.generate_token()
        qr_token_repository.create_token(self.session["id"], token, time.time() - 46)
        with self.assertRaises(TokenExpiredError):
            attendance_service.check_in(token, "STU-1", "device-a")

    def test_token_at_ttl_boundary_accepted(self):
        token = qr_service.generate_token()
        qr_token_repository.create_token(self.session["id"], token, time.time() - 44)
        attendance_service.check_in(token, "STU-1", "device-a")

    def test_unknown_token_rejected(self):
        with self.assertRaises(InvalidTokenError):
            attendance_service.check_in("does-not-exist", "STU-1", "device-a")

    def test_duplicate_student_rejected(self):
        attendance_service.check_in(self._issue(), "STU-1", "device-a")
        with self.assertRaises(DuplicateAttendanceError):
            attendance_service.check_in(self._issue(), "STU-1", "device-b")

    def test_proxy_device_rejected(self):
        attendance_service.check_in(self._issue(), "STU-1", "device-a")
        with self.assertRaises(ProxyDeviceError):
            attendance_service.check_in(self._issue(), "STU-2", "device-a")

    def test_unenrolled_student_rejected(self):
        with self.assertRaises(NotEnrolledError):
            attendance_service.check_in(self._issue(), "STU-9", "device-a")

    def test_closed_session_rejects_tokens_and_check_ins(self):
        token = self._issue()
        session_service.close_session(self.instructor_id, self.session["id"])
        with self.assertRaises(SessionClosedError):
            qr_service.issue_token(self.session["id"], PORT)
        with self.assertRaises(SessionClosedError):
            attendance_service.check_in(token, "STU-1", "device-a")

    def test_other_instructor_cannot_close_session(self):
        with self.assertRaises(PermissionDeniedError):
            session_service.close_session(self.other_instructor_id, self.session["id"])

    def test_roster_csv_export(self):
        attendance_service.check_in(self._issue(), "STU-2", "device-a")
        lines = attendance_service.export_roster_csv(self.session["id"]).splitlines()
        self.assertEqual(lines[0], "student_id,full_name,email,status,checked_in_at")
        self.assertEqual(len(lines), 4)
        statuses = {line.split(",")[0]: line.split(",")[3] for line in lines[1:]}
        self.assertEqual(statuses, {"STU-1": "absent", "STU-2": "present", "STU-3": "absent"})


if __name__ == "__main__":
    unittest.main()
