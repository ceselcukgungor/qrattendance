# CLAUDE.md — QR Attendance System

These rules are strict and apply to every change in this repository.

## Architecture: Layered Architecture (mandatory)

| Layer | Directory | Responsibility |
|---|---|---|
| Presentation | `routes/` | Flask blueprints: HTTP request parsing, response rendering (templates / JSON). No business rules, no SQL. |
| Business Logic | `services/` | Domain rules (token generation, TTL validation, attendance rules). Calls repositories only. |
| Data Access | `repositories/` | All SQL and database connection handling. No HTTP or Flask request objects. |

- Calls flow strictly downward: `routes/` → `services/` → `repositories/`.
- Never bypass layers: routes must never import `repositories/` or `sqlite3`, and must never run SQL.
- Repositories must never import from `services/` or `routes/`.
- `app.py` is only the application factory / wiring point.

## Tech Stack

- Python, Flask
- SQLite with WAL mode enabled (`PRAGMA journal_mode=WAL`) for concurrent read/write operations
- HTML5, CSS3, Vanilla JavaScript (no frontend frameworks, no jQuery)
- `qrcode` (with Pillow) for QR image generation
- Python's built-in `time` module for all token timestamps and TTL checks

## Core Business Rules

- The instructor panel must refresh the QR code asynchronously **every 5 seconds** via JavaScript `fetch` and DOM manipulation — never via full page reloads.
- Every generated token has a **server-side 45-second Time-To-Live (TTL)**, validated with the `time` module (`time.time()`). Client-side timing is never trusted for validation.

## Database

- Schema lives in `repositories/schema.sql`; keep it portable (standard SQL types, explicit foreign keys, no SQLite-only features in table definitions) to ease migration to PostgreSQL or MySQL.
- Use parameterized queries only — never string-format SQL.

## Language

- All code, comments, database schemas, commit messages, and UI text must be written in **English**.
