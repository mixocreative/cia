"""Operator command line.

    python -m runner.cli cancel <job-id>     cancel a job that has not started
    python -m runner.cli digest              print the weekly digest
    python -m runner.cli drain               claim and report one batch, then exit

`drain_batch` in config.yaml is read here and nowhere else; it is the batch size an
operator draining a backlog by hand gets per invocation. README.md documents the command.
"""
from __future__ import annotations

import sys

from . import digest
from .db import connect
from .scheduler import claim_batch, load_config, load_worker_identity


def cancel(conn, job_id: int) -> bool:
    """Cancel a job that has not been claimed.

    The predicate that decided the job is cancellable is repeated in the UPDATE, and the
    affected-row count is what decides the answer — so a worker that claims the job
    between the read and the write wins, and the operator is told no rather than being
    told yes while the job runs.
    """
    row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None or row["status"] != "queued":
        return False

    cur = conn.execute(
        "UPDATE jobs SET status = 'cancelled', finished_at = datetime('now') "
        "WHERE id = ? AND status = 'queued'",
        (job_id,),
    )
    conn.commit()
    return cur.rowcount == 1


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    cfg = load_config()
    conn = connect(cfg.get("db_path", ":memory:"))
    command = argv[0]

    if command == "cancel":
        ok = cancel(conn, int(argv[1]))
        print("cancelled" if ok else "not cancelled - the job is no longer queued")
        return 0 if ok else 1

    if command == "digest":
        print(digest.render(conn))
        return 0

    if command == "drain":
        size = int(cfg.get("drain_batch", 5))
        identity = load_worker_identity()
        claimed = claim_batch(conn, worker=identity["name"], limit=size)
        print(f"drain: claimed {len(claimed)} of at most {size}")
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
