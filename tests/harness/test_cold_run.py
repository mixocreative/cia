"""Tests for cold_run.py. The RUNBOOK is injected via CIA_RUNBOOK so results do not
depend on another editor's progress on the live RUNBOOK."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "cold_run.py"

HARD = (
    "HARD RULES:\n"
    "- Do not read `tests/corpus/entries/`, `tests/EXPECTED-*.md` or `tests/RUNS.md` - key.\n"
    "- You MAY and SHOULD read the skill's own `references/*.md`."
)

RUNBOOK_BASE = (
    "# Runbook\n\n## Procedure\n\n"
    "2. **Trigger.** Say exactly: `pre-launch audit, Screen tier`. Then `run tests` alone.\n\n"
    "### The hard rule in the prompt fences the oracle\n\n```\n" + HARD + "\n```\n"
)
BUILD_SECTION = "\n## The build-mode run\n\n```\nbuild a thing\n```\n"


def run(mode, runbook_text, extra=()):
    with tempfile.TemporaryDirectory() as d:
        rb = Path(d) / "RUNBOOK.md"
        rb.write_text(runbook_text, encoding="utf-8")
        env = dict(os.environ, CIA_RUNBOOK=str(rb))
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--mode", mode, *extra],
            capture_output=True, text=True, env=env,
        )


def prompt_of(res):
    cmd = json.loads(res.stdout.split("\n")[0])
    return cmd[2]


class ColdRunTests(unittest.TestCase):
    def test_audit_dry_run_carries_hard_rules_and_key_exclusion(self):
        res = run("audit", RUNBOOK_BASE, ["--dry-run"])
        self.assertEqual(res.returncode, 0, res.stderr)
        p = prompt_of(res)
        self.assertTrue(p.startswith("pre-launch audit, Screen tier"))
        self.assertIn(HARD, p)
        self.assertIn("tests/EXPECTED-", p)

    def test_run_tests_prompt_starts_with_run_tests(self):
        res = run("run-tests", RUNBOOK_BASE, ["--dry-run"])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(prompt_of(res).startswith("run tests"))

    def test_build_without_section_exits_2(self):
        res = run("build", RUNBOOK_BASE, ["--dry-run"])
        self.assertEqual(res.returncode, 2)
        self.assertIn("build-mode run", res.stderr)

    def test_build_with_section_dry_run_ok(self):
        res = run("build", RUNBOOK_BASE + BUILD_SECTION, ["--dry-run"])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(prompt_of(res).startswith("build a thing"))

    def test_malformed_mode_exits_2(self):
        res = run("bogus", RUNBOOK_BASE, ["--dry-run"])
        self.assertEqual(res.returncode, 2)

    def test_audit_cannot_write_build_can(self):
        # The allow-list enforces "do not modify the fixture"; only build mode (on a copy) may edit.
        def tools(mode, text):
            cmd = json.loads(run(mode, text, ["--dry-run"]).stdout.split("\n")[0])
            return cmd[cmd.index("--allowedTools") + 1:]
        for mode in ("audit", "run-tests"):
            t = tools(mode, RUNBOOK_BASE)
            self.assertNotIn("Write", t)
            self.assertNotIn("Edit", t)
            self.assertIn("Bash(python:*)", t)
        b = tools("build", RUNBOOK_BASE + BUILD_SECTION)
        self.assertIn("Write", b)
        self.assertIn("Edit", b)


if __name__ == "__main__":
    unittest.main()
