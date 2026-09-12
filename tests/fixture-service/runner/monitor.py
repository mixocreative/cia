"""Every 5 minutes: is every worker alive, and is any job stuck?"""
from __future__ import annotations

import datetime as dt
import sqlite3
import sys


def stuck_jobs(conn: sqlite3.Connection, minutes: int) -> list[sqlite3.Row]:
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=minutes)).isoformat()
    return conn.execute(
        "SELECT id, kind, claimed_by, started_at FROM jobs WHERE status = 'running' AND started_at < ?",
        (cutoff,),
    ).fetchall()


def check(conn: sqlite3.Connection, cfg: dict) -> int:
    """Print one summary line. Exit 0 unless something is definitely wrong."""
    problems = 0
    unknown = 0

    workers = conn.execute("SELECT name, last_seen FROM workers").fetchall()
    for w in workers:
        try:
            age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(w["last_seen"])
        except ValueError:
            unknown += 1
            continue
        if age > dt.timedelta(minutes=10):
            problems += 1
            print(f"worker {w['name']} last seen {age} ago", file=sys.stderr)

    for job in stuck_jobs(conn, cfg["stuck_after_minutes"]):
        problems += 1
        print(f"job {job['id']} ({job['kind']}) running since {job['started_at']}", file=sys.stderr)

    print(f"monitor: {problems} problems")
    return 0 if problems == 0 else 1
