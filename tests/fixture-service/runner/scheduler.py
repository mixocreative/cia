"""Claim queued jobs and run them. One scheduler process per worker."""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

DEFAULTS = {"retry_limit": 3, "stuck_after_minutes": 30, "alerts_enabled": True}


def load_config(path: str = "config.yaml") -> dict:
    """Read the flat key: value config. Falls back to defaults if anything goes wrong."""
    try:
        cfg = dict(DEFAULTS)
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, value = (s.strip() for s in line.split(":", 1))
            if value in ("true", "false"):
                cfg[key] = value == "true"
            elif value.isdigit():
                cfg[key] = int(value)
            else:
                cfg[key] = value
        return cfg
    except Exception:  # noqa: BLE001 - config is optional in dev
        return dict(DEFAULTS)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def enqueue(conn: sqlite3.Connection, kind: str, idempotency_key: str) -> int | None:
    """Insert a job once per idempotency key; a repeat submit returns None instead of a duplicate."""
    try:
        cur = conn.execute(
            "INSERT INTO jobs (kind, status, idempotency_key) VALUES (?, 'queued', ?)",
            (kind, idempotency_key),
        )
        conn.commit()
        return int(cur.lastrowid)
    except sqlite3.IntegrityError:
        return None


def claim_batch(conn: sqlite3.Connection, worker: str, limit: int = 10) -> list[int]:
    """Take up to `limit` queued jobs for this worker."""
    rows = conn.execute(
        "SELECT id FROM jobs WHERE status = 'queued' ORDER BY id LIMIT ?", (limit,)
    ).fetchall()
    claimed: list[int] = []
    for row in rows:
        conn.execute(
            "UPDATE jobs SET status = 'running', claimed_by = ?, started_at = ?, attempts = attempts + 1 "
            "WHERE id = ?",
            (worker, now(), row["id"]),
        )
        claimed.append(int(row["id"]))
    conn.commit()
    return claimed


def finish(conn: sqlite3.Connection, job_id: int, ok: bool, error: str | None, cfg: dict) -> None:
    if ok:
        conn.execute(
            "UPDATE jobs SET status = 'done', finished_at = ? WHERE id = ?", (now(), job_id)
        )
    else:
        attempts = conn.execute("SELECT attempts FROM jobs WHERE id = ?", (job_id,)).fetchone()["attempts"]
        status = "failed" if attempts >= cfg["retry_limit"] else "queued"
        conn.execute(
            "UPDATE jobs SET status = ?, last_error = ? WHERE id = ?", (status, error, job_id)
        )
    conn.commit()


def heartbeat(conn: sqlite3.Connection, worker: str, cfg: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO workers (name, last_seen) VALUES (?, ?)", (worker, now())
    )
    conn.commit()
    Path(str(cfg.get("heartbeat_path", "/tmp/heartbeat"))).parent.mkdir(parents=True, exist_ok=True)
    Path(str(cfg.get("heartbeat_path", "/tmp/heartbeat"))).write_text(now(), encoding="utf-8")
