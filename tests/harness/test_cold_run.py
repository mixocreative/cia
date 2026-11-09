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
        self.assertEqual(cmd[cmd.index("-s") + 1], "danger-full-access")  # owner decision; safe only on a copy
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


def cmd_of(res):
    return json.loads(res.stdout.split("\n")[0])


class ArmTests(unittest.TestCase):
    """A comparison arm is the same task with the skill swapped out, and it must not reach cia."""

    def test_no_skill_arm_cannot_read_the_skill(self):
        res = run("audit", RUNBOOK_BASE, ["--dry-run", "--arm", "none"])
        self.assertEqual(res.returncode, 0, res.stderr)
        p, cmd = prompt_of(res), cmd_of(res)
        self.assertTrue(p.startswith("pre-launch audit, Screen tier"))  # the task text is identical
        self.assertIn(HARD, p)
        self.assertNotIn("S:\\ai\\skills\\cia", p)
        self.assertIn("No skill is provided", p)
        tools = cmd[cmd.index("--allowedTools") + 1:]
        self.assertIn("--disable-slash-commands", cmd)
        self.assertIn("Read(./**)", tools)
        self.assertNotIn("Read", tools)   # an unscoped Read would reach S:\ai\skills\cia
        self.assertNotIn("Skill", tools)
        self.assertIn("Bash(node:*)", tools)  # the same runtime walk as a cia run

    def test_ponytail_arm_carries_the_pinned_instructions(self):
        p = prompt_of(run("audit", RUNBOOK_BASE, ["--dry-run", "--arm", "ponytail"]))
        self.assertIn("ponytail-audit at 96608e0", p)
        self.assertIn("## 1. Map first", p)
        self.assertNotIn("name: ponytail-audit", p)  # frontmatter dropped
        self.assertNotIn("S:\\ai\\skills\\cia", p)

    def test_arms_are_audits_only(self):
        self.assertEqual(run("build", RUNBOOK_BASE + BUILD_SECTION, ["--dry-run", "--arm", "none"]).returncode, 2)
        self.assertEqual(run("audit", RUNBOOK_BASE, ["--dry-run", "--arm", "none", "--runtime", "codex"]).returncode, 2)

    def test_cia_traces_names_skill_vocabulary(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        self.assertEqual(cold_run.cia_traces("Must fix: the claim races."), [])
        self.assertEqual(cold_run.cia_traces("per references/sweeps.md §3"), ["references/", "§"])


class HeaderFactTests(unittest.TestCase):
    """The header names the model that answered and how much of the skill the report quotes."""

    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        self.cr = cold_run

    def test_json_result_yields_report_model_cost_turns(self):
        text, facts = self.cr.claude_result(json.dumps(
            {"result": "report", "modelUsage": {"claude-sonnet-5-5": {}}, "total_cost_usd": 0.4, "num_turns": 9}))
        self.assertEqual(text, "report")
        self.assertEqual(facts, {"resolved": "claude-sonnet-5-5", "cost": 0.4, "turns": 9})

    def test_non_json_output_is_kept_whole(self):
        self.assertEqual(self.cr.claude_result("plain report"), ("plain report", {}))

    def test_receipts_are_counted_against_the_skill(self):
        quoted, total = self.cr.receipts_quoted("the channel is the finding", self.cr.REPO)
        self.assertEqual(quoted, 1)
        self.assertGreater(total, 10)


class PartialReadTests(unittest.TestCase):
    """A receipt can be quoted after jumping to a file's last line; the admission is what we can count."""

    def test_admissions_are_counted_and_plain_reads_are_not(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        self.assertEqual(cold_run.partial_reads(
            "For these five I read only the closing receipt line, not the whole file.\n"
            "browser-walks.md (read §12–14 only; §1–11 by heading only)\n"
            "theory.md read in full."), 2)
        self.assertEqual(cold_run.partial_reads("Reference receipts: sweeps/ \"the channel is the finding\""), 0)

    def test_sweep_sites_counts_enumerated_lines_only(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        report = ("S3 swept, 1 finding, sites: app/a.py:4, app/b.py:9 (❌ F2)\n"
                  "S21: ❌ F7\n"                                  # a finding ref in place of the list
                  "| RUN-4 | S21 | `tests/t.py:9` |\n"             # a finding row is not a sweep line
                  "- **S5:** posture per site:\n"
                  "  - `config.py:12` read, no consumer.\n"       # an indented site belongs to S5
                  "S9 swept, 0 findings, sites: none\n"           # no path: not evidenced
                  "   - **2a. Sweeps:**\n"
                  "     - S2 F1, F10.\n"                          # nested, refs only
                  "     - S1 swept, 0 findings (`scheduler.py:78`).\n")  # nested, with a site
        self.assertEqual(cold_run.sweep_sites(report), 3)

    def test_refs_opened_names_each_reference_once(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        log = ("exec\npwsh -Command \"Get-Content S:\\ai\\skills\\cia\\references\\reporting.md\" in C:\\tmp\n"
               " succeeded in 20ms:\n| `references/theory.md` | Step 2 |\n"   # file output naming another ref
               "exec\ncat references/sweeps/04-enumeration-environment-liveness.md in C:\\tmp\n"
               "exec\nrg receipt references/reporting.md in C:\\tmp\n"
               "exec\npython -c \"root=Path(r'S:\\\\ai\\\\skills\\\\cia\\\\references'); names=['evidence.md']\" in C:\\tmp\n")
        names = ["evidence.md", "reporting.md", "theory.md", "sweeps/04-enumeration-environment-liveness.md"]
        self.assertEqual(cold_run.refs_opened(log, names),   # theory.md appears only in output: not opened
                         ["evidence.md", "reporting.md", "sweeps/04-enumeration-environment-liveness.md"])


class LeftoverTests(unittest.TestCase):
    """A run that leaves a process behind is reported; a listing that failed is n/r, never 0."""

    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        self.cr = cold_run

    def test_orphans_and_copy_processes_are_reported_and_old_or_parented_ones_are_not(self):
        after = [
            {"pid": 1, "ppid": 0, "cmd": "explorer.exe"},                                # existed before
            {"pid": 10, "ppid": 1, "cmd": "notepad.exe"},                                # new, parent alive
            {"pid": 11, "ppid": 999, "cmd": "graphify watch runner"},                    # new, orphaned
            {"pid": 12, "ppid": 1, "cmd": r"node C:\Temp\cia-audit-abc\server.js"},      # new, names the copy
        ]
        got = self.cr.leftovers({0, 1}, after, r"C:\TEMP\cia-audit-abc")
        self.assertEqual([p["pid"] for p in got], [11, 12])

    def test_live_listing_includes_this_process(self):
        procs = self.cr.list_processes()
        self.assertIsNotNone(procs)
        self.assertIn(os.getpid(), {p["pid"] for p in procs})


class EgmTests(unittest.TestCase):
    def test_egm_runs_one_read_only_goldfish(self):
        res = run("egm", RUNBOOK_BASE, ["--dry-run", "--doc", "references/journey-map.md", "--reviewer", "structural"])
        self.assertEqual(res.returncode, 0, res.stderr)
        cmd = cmd_of(res)
        self.assertEqual(cmd[cmd.index("--agent") + 1], "egm:egm-structural")
        self.assertEqual(cmd[cmd.index("--allowedTools") + 1:], ["Read", "Grep", "Glob"])
        self.assertIn("Document: references/journey-map.md", cmd[2])
        self.assertIn("Findings: <blockers>/<majors>/<nits>", cmd[2])

    def test_egm_refuses_a_document_outside_the_skill(self):
        self.assertEqual(run("egm", RUNBOOK_BASE, ["--dry-run", "--doc", "../README.md"]).returncode, 2)
        self.assertEqual(run("egm", RUNBOOK_BASE, ["--dry-run"]).returncode, 2)

if __name__ == "__main__":
    unittest.main()
