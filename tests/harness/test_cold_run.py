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
            self.assertIn("Bash(node:*)", t)  # a Node fixture's runtime walk; without it every probe is blocked
        b = tools("build", RUNBOOK_BASE + BUILD_SECTION)
        self.assertIn("Write", b)
        self.assertIn("Edit", b)

    def test_prompt_states_the_permission_shape(self):
        # Without it, runs wrap node in `cd && ...` and the headless allow-list refuses the whole walk.
        self.assertIn("no `cd ... &&`", prompt_of(run("audit", RUNBOOK_BASE, ["--dry-run"])))

    def test_every_mode_runs_on_a_copy(self):
        # An audit's runtime walk writes the fixture's state; no mode may run in the repo fixture.
        for mode, text in (("audit", RUNBOOK_BASE), ("run-tests", RUNBOOK_BASE),
                           ("build", RUNBOOK_BASE + BUILD_SECTION)):
            res = run(mode, text, ["--dry-run"])
            self.assertIn(f"cwd: {os.path.join(tempfile.gettempdir(), f'cia-{mode}-<new-copy>')}", res.stdout)



class CodexTests(unittest.TestCase):
    def test_codex_runs_on_a_copy_with_checked_flags(self):
        res = run("audit", RUNBOOK_BASE, ["--dry-run", "--runtime", "codex"])
        self.assertEqual(res.returncode, 0, res.stderr)
        cmd = json.loads(res.stdout.split(chr(10))[0])
        self.assertEqual(cmd[:2], ["codex", "exec"])
        self.assertIn("--skip-git-repo-check", cmd)
        self.assertEqual(cmd[cmd.index("-s") + 1], "workspace-write")
        self.assertTrue(cmd[-1].startswith("pre-launch audit, Screen tier"))
        self.assertIn("cia-audit-<new-copy>", res.stdout)  # never the repo fixture


class SiblingSkillTests(unittest.TestCase):
    def test_skill_root_points_at_its_own_fixture_and_skill(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "other-skill"
            (root / "tests" / "shop").mkdir(parents=True)
            (root / "tests" / "RUNBOOK.md").write_text(RUNBOOK_BASE, encoding="utf-8")
            res = subprocess.run([sys.executable, str(SCRIPT), "--mode", "audit", "--dry-run",
                                  "--skill-root", str(root), "--fixture", "shop"],
                                 capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn(str(root / "tests" / "shop"), res.stdout)
            self.assertIn(str(root.resolve()), prompt_of(res))

    def test_missing_fixture_exits_2(self):
        res = run("audit", RUNBOOK_BASE, ["--dry-run", "--fixture", "no-such-fixture"])
        self.assertEqual(res.returncode, 2)

if __name__ == "__main__":
    unittest.main()
