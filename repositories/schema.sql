-- QR Attendance relational schema.
-- Portability notes (PostgreSQL / MySQL migration):
--   * "INTEGER PRIMARY KEY" auto-increments in SQLite; map to SERIAL/IDENTITY (PostgreSQL)
--     or INT AUTO_INCREMENT (MySQL).
--   * Epoch timestamps from Python's time.time() are stored as DOUBLE PRECISION,
--     which is supported by SQLite, PostgreSQL, and MySQL.
--   * Only standard types, CHECK constraints, and explicit foreign keys are used.

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    institution_id  VARCHAR(32)  NOT NULL UNIQUE,
    full_name       VARCHAR(120) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(16)  NOT NULL CHECK (role IN ('instructor', 'student')),
    created_at      DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id              INTEGER PRIMARY KEY,
    code            VARCHAR(32)  NOT NULL UNIQUE,
    title           VARCHAR(200) NOT NULL,
    instructor_id   INTEGER      NOT NULL,
    created_at      DOUBLE PRECISION NOT NULL,
    FOREIGN KEY (instructor_id) REFERENCES users (id)
);

-- Student-to-course assignments (many-to-many).
CREATE TABLE IF NOT EXISTS course_enrollments (
    course_id       INTEGER NOT NULL,
    student_id      INTEGER NOT NULL,
    enrolled_at     DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (course_id, student_id),
    FOREIGN KEY (course_id)  REFERENCES courses (id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users (id)   ON DELETE CASCADE
);

-- A single class meeting during which attendance is taken.
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY,
    course_id       INTEGER     NOT NULL,
    started_at      DOUBLE PRECISION NOT NULL,
    ended_at        DOUBLE PRECISION,
    status          VARCHAR(16) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- Rotating QR tokens; each token has a server-side TTL (expires_at = issued_at + 45).
CREATE TABLE IF NOT EXISTS qr_tokens (
    id              INTEGER PRIMARY KEY,
    session_id      INTEGER     NOT NULL,
    token           VARCHAR(64) NOT NULL UNIQUE,
    issued_at       DOUBLE PRECISION NOT NULL,
    expires_at      DOUBLE PRECISION NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id              INTEGER PRIMARY KEY,
    session_id      INTEGER NOT NULL,
    student_id      INTEGER NOT NULL,
    token_id        INTEGER,
    recorded_at     DOUBLE PRECISION NOT NULL,
    UNIQUE (session_id, student_id),
    FOREIGN KEY (session_id) REFERENCES sessions (id)  ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users (id)     ON DELETE CASCADE,
    FOREIGN KEY (token_id)   REFERENCES qr_tokens (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_courses_instructor   ON courses (instructor_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student  ON course_enrollments (student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_course      ON sessions (course_id);
CREATE INDEX IF NOT EXISTS idx_qr_tokens_session    ON qr_tokens (session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student   ON attendance_records (student_id);
