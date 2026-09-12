import os
import unittest

from runner import db, monitor, scheduler


class SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = db.connect()
        self.cfg = dict(scheduler.DEFAULTS)

    def test_enqueue_is_idempotent(self) -> None:
        first = scheduler.enqueue(self.conn, "email", "key-1")
        second = scheduler.enqueue(self.conn, "email", "key-1")
        self.assertIsNotNone(first)
        self.assertIsNone(second)

    def test_claim_moves_queued_to_running(self) -> None:
        scheduler.enqueue(self.conn, "email", "key-2")
        claimed = scheduler.claim_batch(self.conn, "w1")
        self.assertEqual(len(claimed), 1)
        status = self.conn.execute("SELECT status FROM jobs WHERE id = ?", (claimed[0],)).fetchone()[0]
        self.assertEqual(status, "running")

    def test_no_jobs_are_stuck_on_a_fresh_db(self) -> None:
        scheduler.enqueue(self.conn, "email", "key-3")
        scheduler.claim_batch(self.conn, "w1")
        self.assertEqual(monitor.stuck_jobs(self.conn, minutes=30), [])

    def test_config_from_real_file(self) -> None:
        cfg = scheduler.load_config(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
        os.environ["FIXTURE_ALERTS"] = str(cfg["alerts_enabled"])
        self.assertEqual(cfg["retry_limit"], 3)


if __name__ == "__main__":
    unittest.main()
