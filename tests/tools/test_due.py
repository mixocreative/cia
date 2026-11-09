"""Guard tests for tools/due.py's pure rules: when an arm comparison or an EGM review is due."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import due  # noqa: E402

ARMS = """# ARMS
| Date | Skill commit | Arm | Model |
|---|---|---|---|
| 2026-11-09 | `abc1234` | none | sonnet |
| 2026-11-10 | `def5678` (run at `9999999`) | ponytail | sonnet |
"""

EGM = """| Date | Commit | Document | Reviewer |
|---|---|---|---|
| 2026-11-09 | `c8ac18a` | `references/journey-map.md` | comprehension |
| 2026-11-12 | `1111111` | references/journey-map.md | structural |
"""


class DueTests(unittest.TestCase):
    def test_rows_are_dated_lines_only(self):
        self.assertEqual(len(due.table_rows(ARMS)), 2)

    def test_newest_arm_commit_is_the_first_hash_of_the_last_row(self):
        self.assertEqual(due.newest_arm_commit(due.table_rows(ARMS)), "def5678")
        self.assertIsNone(due.newest_arm_commit([]))

    def test_no_arm_row_is_due(self):
        self.assertEqual(len(due.arms_reasons(None, None, 4000, False)), 1)

    def test_growth_under_the_threshold_is_not_due(self):
        self.assertEqual(due.arms_reasons("abc1234", 4000, 4399, False), [])

    def test_growth_at_the_threshold_is_due(self):
        self.assertIn("grew 10%", due.arms_reasons("abc1234", 4000, 4400, False)[0])

    def test_a_changed_key_makes_the_baseline_stale(self):
        self.assertIn("answer key", due.arms_reasons("abc1234", 4000, 4000, True)[0])

    def test_newest_review_per_document_wins(self):
        self.assertEqual(due.reviewed_at(due.table_rows(EGM)), {"references/journey-map.md": "1111111"})

    def test_egm_threshold_and_order(self):
        got = due.egm_due({"a.md": 19, "b.md": 20, "c.md": 80})
        self.assertEqual(got, [("c.md", 80), ("b.md", 20)])


if __name__ == "__main__":
    unittest.main()
