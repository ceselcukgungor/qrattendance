# Architecture

## Layered Architecture

| Layer | Directory | Responsibility |
|---|---|---|
| Presentation | `routes/` | Flask blueprints: request parsing and response rendering (templates or JSON). No business rules, no SQL. |
| Business Logic | `services/` | Domain rules: token generation, TTL validation, enrollment and anti-proxy checks, statistics. Calls repositories only. |
| Data Access | `repositories/` | All SQL and connection handling. No Flask or HTTP objects. |

- Dependencies flow strictly downward: `routes/` → `services/` → `repositories/`.
- Routes never import `repositories/` or `sqlite3` and never execute SQL.
- Repositories never import from `services/` or `routes/`.
- `app.py` is only the application factory and wiring point.

## Tech Stack

- Python, Flask
- SQLite with WAL mode (`PRAGMA journal_mode=WAL`) for concurrent reads and writes
- HTML5, CSS3, Vanilla JavaScript (no frontend frameworks)
- `qrcode` with Pillow for QR image generation
- Python's built-in `time` module for all timestamps and TTL checks

## Business Rules

- The instructor panel refreshes the QR code asynchronously every 5 seconds via `fetch` and DOM updates, never by reloading the page.
- Each token has a server-side TTL of 45 seconds: a token is valid only while `time.time() - created_at <= 45.0`. Client-side timing is never trusted.
- Tokens cannot be issued and check-ins cannot be recorded for closed sessions.
- A student may check in only to sessions of courses they are enrolled in, and only once per session.
- A device token may be used for only one student per session (anti-proxy rule).

## Database

- The schema lives in `repositories/schema.sql` and uses portable SQL (standard types, explicit foreign keys) to ease migration to PostgreSQL or MySQL.
- Uniqueness rules are enforced by constraints in addition to service-level checks, so concurrent requests cannot bypass them.
- Queries are always parameterized.

## Conventions

- All code, comments, schemas, commit messages, and UI text are in English.
- Docstrings are short and technical; comments explain intent only where it is not obvious.
