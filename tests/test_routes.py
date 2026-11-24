"""Integration tests for the HTTP layer using the Flask test client."""
import os
import tempfile
import time
import unittest
from urllib.parse import parse_qs, urlparse

from werkzeug.security import generate_password_hash

from app import create_app
from repositories import course_repository, qr_token_repository, user_repository
from services import qr_service

PASSWORD = "test-password"


class RoutesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_PATH": os.path.join(self._tmp.name, "test.db"),
            "CHECKIN_HOST": "127.0.0.1",
        })

        password_hash = generate_password_hash(PASSWORD)
        instructor_id = user_repository.create_user(
            "INS-1", "Test Instructor", "ins1@example.test", password_hash, "instructor"
        )
        user_repository.create_user(
            "INS-2", "Other Instructor", "ins2@example.test", password_hash, "instructor"
        )
        self.course_id = course_repository.create_course("CS101", "Programming", instructor_id)
        for number in (1, 2, 3):
            student_pk = user_repository.create_user(
                f"STU-{number}", f"Student {number}", f"s{number}@example.test", password_hash, "student"
            )
            course_repository.enroll_student(self.course_id, student_pk)
        user_repository.create_user("STU-9", "Outsider", "s9@example.test", password_hash, "student")

        self.instructor = self.app.test_client()

    def tearDown(self):
        self._tmp.cleanup()

    def _login(self, client, institution_id="INS-1", password=PASSWORD):
        return client.post("/login", data={"institution_id": institution_id, "password": password})

    def _start_session(self):
        self._login(self.instructor)
        response = self.instructor.post("/api/sessions/start", json={"course_id": self.course_id})
        self.assertEqual(response.status_code, 201)
        return response.get_json()["session_id"]

    def _poll_qr(self, session_id):
        response = self.instructor.get(f"/api/sessions/{session_id}/qr")
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def _current_token(self, session_id):
        url = self._poll_qr(session_id)["checkin_url"]
        return parse_qs(urlparse(url).query)["token"][0]

    @staticmethod
    def _check_in(client, token, student_id):
        return client.post("/api/attendance/checkin", json={"token": token, "student_id": student_id})

    def test_login_success_and_dashboard(self):
        response = self._login(self.instructor)
        self.assertEqual(response.status_code, 302)
        page = self.instructor.get("/instructor")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"CS101", page.data)

    def test_login_rejects_bad_password_and_students(self):
        self.assertEqual(self._login(self.instructor, password="wrong").status_code, 401)
        self.assertEqual(self._login(self.instructor, institution_id="STU-1").status_code, 401)

    def test_api_requires_login(self):
        response = self.app.test_client().post("/api/sessions/start", json={"course_id": self.course_id})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.app.test_client().get("/instructor").status_code, 302)

    def test_start_session_validates_course_id(self):
        self._login(self.instructor)
        response = self.instructor.post("/api/sessions/start", json={"course_id": "abc"})
        self.assertEqual(response.status_code, 400)

    def test_other_instructor_cannot_access_session(self):
        session_id = self._start_session()
        other = self.app.test_client()
        self._login(other, institution_id="INS-2")
        self.assertEqual(other.get(f"/api/sessions/{session_id}/qr").status_code, 403)

    def test_qr_polling_returns_fresh_image_and_stats(self):
        session_id = self._start_session()
        first = self._poll_qr(session_id)
        second = self._poll_qr(session_id)
        self.assertTrue(first["qr_image"].startswith("data:image/png;base64,"))
        self.assertNotEqual(first["checkin_url"], second["checkin_url"])
        self.assertEqual(first["session_status"], "active")
        self.assertEqual((first["present_count"], first["total_enrolled"]), (0, 3))
        self.assertEqual((first["attendance_rate"], first["absenteeism_rate"]), (0.0, 100.0))

    def test_checkin_page_renders_token(self):
        response = self.app.test_client().get("/checkin?token=abc123")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="abc123"', response.data)

    def test_valid_check_in_sets_device_cookie(self):
        session_id = self._start_session()
        student = self.app.test_client()
        response = self._check_in(student, self._current_token(session_id), "STU-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["student_id"], "STU-1")
        cookie_header = response.headers.get("Set-Cookie", "")
        self.assertIn("device_token=", cookie_header)
        self.assertIn("HttpOnly", cookie_header)

        attendance = self.instructor.get(f"/api/sessions/{session_id}/attendance").get_json()
        self.assertEqual([s["student_id"] for s in attendance["students"]], ["STU-1"])
        self.assertEqual(attendance["present_count"], 1)
        self.assertEqual(attendance["attendance_rate"], 33.3)

    def test_expired_and_invalid_tokens_rejected(self):
        session_id = self._start_session()
        expired = qr_service.generate_token()
        qr_token_repository.create_token(session_id, expired, time.time() - 46)

        response = self._check_in(self.app.test_client(), expired, "STU-1")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "token_expired")

        response = self._check_in(self.app.test_client(), "not-a-real-token", "STU-1")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "invalid_token")

    def test_proxy_device_blocked_by_cookie(self):
        session_id = self._start_session()
        device = self.app.test_client()
        self.assertEqual(self._check_in(device, self._current_token(session_id), "STU-1").status_code, 200)

        response = self._check_in(device, self._current_token(session_id), "STU-2")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "proxy_device")

    def test_duplicate_and_unenrolled_students_rejected(self):
        session_id = self._start_session()
        self._check_in(self.app.test_client(), self._current_token(session_id), "STU-1")

        duplicate = self._check_in(self.app.test_client(), self._current_token(session_id), "STU-1")
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(duplicate.get_json()["error"], "duplicate_attendance")

        outsider = self._check_in(self.app.test_client(), self._current_token(session_id), "STU-9")
        self.assertEqual(outsider.status_code, 400)
        self.assertEqual(outsider.get_json()["error"], "not_enrolled")

    def test_csv_export(self):
        session_id = self._start_session()
        self._check_in(self.app.test_client(), self._current_token(session_id), "STU-2")

        response = self.instructor.get(f"/api/sessions/{session_id}/export")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.mimetype == "text/csv")
        self.assertIn("attachment", response.headers["Content-Disposition"])
        lines = response.get_data(as_text=True).splitlines()
        self.assertEqual(lines[0], "student_id,full_name,email,status,checked_in_at")
        self.assertEqual(len(lines), 4)

    def test_end_session_stops_tokens_and_check_ins(self):
        session_id = self._start_session()
        token = self._current_token(session_id)

        response = self.instructor.post(f"/api/sessions/{session_id}/end")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "closed")

        snapshot = self._poll_qr(session_id)
        self.assertEqual(snapshot["session_status"], "closed")
        self.assertIsNone(snapshot["qr_image"])

        check_in = self._check_in(self.app.test_client(), token, "STU-1")
        self.assertEqual(check_in.status_code, 403)
        self.assertEqual(check_in.get_json()["error"], "session_closed")

        self.assertEqual(self.instructor.post(f"/api/sessions/{session_id}/end").status_code, 403)


if __name__ == "__main__":
    unittest.main()
