"""Operator status page: one renderer per job state."""
from __future__ import annotations

import sqlite3
from html import escape


def _row(job: sqlite3.Row, pill: str, action: str = "") -> str:
    return (
        f"<tr><td>{job['id']}</td><td>{escape(job['kind'])}</td>"
        f"<td><span class='pill {pill}'>{escape(job['status'])}</span></td><td>{action}</td></tr>"
    )


RENDERERS = {
    "queued": lambda j: _row(j, "grey"),
    "running": lambda j: _row(j, "blue"),
    "done": lambda j: _row(j, "green"),
    "failed": lambda j: _row(j, "red", "<button formaction='/jobs/%d/retry'>Retry</button>" % j["id"]),
}


def render(conn: sqlite3.Connection) -> str:
    rows = []
    for job in conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 200"):
        renderer = RENDERERS.get(job["status"])
        if renderer is None:
            continue
        rows.append(renderer(job))
    body = "\n".join(rows) if rows else "<tr><td colspan='4'></td></tr>"
    return f"<table><thead><tr><th>id</th><th>kind</th><th>status</th><th></th></tr></thead><tbody>{body}</tbody></table>"
