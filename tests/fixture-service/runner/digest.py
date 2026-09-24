"""Weekly operator digest — a read-only summary of what the queue did.

D4 in docs/ARCHITECTURE.md governs this module: the digest is a convenience, never a
control, so it degrades rather than fails. Nothing acts on its output and nothing is
recorded as handled because it rendered.
"""
from __future__ import annotations

import sqlite3


def render(conn: sqlite3.Connection) -> str:
    """Return a one-line digest, or a stated degradation.

    The catch here is deliberate and is the choice D4 names: this is a display path, the
    caller is a human reading a summary, and a failed digest must not take down the page
    that carries it. The degradation is *visible* — it says the number is unavailable
    rather than printing a zero, which would be indistinguishable from a quiet week.
    """
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"
        ).fetchall()
    except sqlite3.Error as exc:  # display path, per D4
        return f"digest unavailable ({exc.__class__.__name__}) - the queue itself is unaffected"

    if not rows:
        return "digest: no jobs have been submitted yet"

    parts = ", ".join(f"{r['n']} {r['status']}" for r in rows)
    return f"digest: {parts}"
