"""Guard tests for tools/receipts.py: every reference has a unique receipt, and none leaks into SKILL.md.

Why the leak test: SKILL.md's example line quoted six real receipts until 2026-11-10, so a run that read
only SKILL.md could copy them and pass audit_report.py without opening a reference.
"""
import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import receipts  # noqa: E402


class ReceiptTests(unittest.TestCase):
    def test_repo_passes_the_gate(self):
        argv = sys.argv
        sys.argv = ["receipts.py", "--gate"]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(receipts.main(), 0)
        finally:
            sys.argv = argv

    def test_a_receipt_quoted_in_skill_is_a_leak(self):
        found = {"theory.md": "a codebase has five systems", "doctrine.md": "an invariant is a sentence"}
        text = 'Reference receipts: theory.md "a codebase has five systems" | doctrine.md "<its receipt>"'
        self.assertEqual(receipts.leaked(found, text), [("theory.md", "a codebase has five systems")])

    def test_skill_quotes_no_real_receipt(self):
        found, _ = receipts.scan()
        skill = (receipts.HERE / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(receipts.leaked(found, skill), [])


if __name__ == "__main__":
    unittest.main()
