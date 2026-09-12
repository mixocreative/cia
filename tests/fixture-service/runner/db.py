"""SQLite storage for the job runner."""
from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY,
    kind          TEXT NOT NULL,
    status        TEXT NOT NULL,           -- queued, running, done, failed, stuck
    attempts      INTEGER NOT NULL DEFAULT 0,
    idempotency_key TEXT NOT NULL UNIQUE,  -- verified control: one key, one job
    claimed_by    TEXT,
    started_at    TEXT,
    finished_at   TEXT,
    last_error    TEXT
);

CREATE TABLE IF NOT EXISTS workers (
    name       TEXT PRIMARY KEY,
    last_seen  TEXT NOT NULL
);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
