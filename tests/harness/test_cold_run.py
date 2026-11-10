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

    def test_effort_is_passed_to_codex_and_refused_for_claude(self):
        res = run("audit", RUNBOOK_BASE, ["--dry-run", "--runtime", "codex", "--effort", "high"])
        cmd = json.loads(res.stdout.split(chr(10))[0])
        self.assertEqual(cmd[cmd.index("-c") + 1], "model_reasoning_effort=high")
        self.assertTrue(cmd[-1].startswith("pre-launch audit, Screen tier"))  # the prompt stays last
        self.assertEqual(run("audit", RUNBOOK_BASE, ["--dry-run", "--effort", "high"]).returncode, 2)


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
        self.assertEqual(facts, {"resolved": "claude-sonnet-5-5", "cost": 0.4, "turns": 9, "session": None})

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

    def test_the_copy_never_carries_git_history(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "src", Path(d) / "dst"
            (src / ".git").mkdir(parents=True)
            (src / ".git" / "HEAD").write_text("fix commit", encoding="utf-8")
            (src / "a.py").write_text("x = 1\n", encoding="utf-8")
            self.cr.copy_fixture(src, dst)
            self.assertTrue((dst / "a.py").exists())
            self.assertFalse((dst / ".git").exists())

    def test_only_processes_naming_the_runs_copy_are_stopped(self):
        left = [{"pid": 11, "ppid": 999, "cmd": "graphify watch runner"},                   # orphan, unattributable
                {"pid": 12, "ppid": 999, "cmd": r"graphify watch C:\Temp\cia-audit-abc"},   # names this run's copy
                {"pid": 13, "ppid": 999, "cmd": r"graphify watch C:\Temp\cia-audit-xyz"}]   # another run's copy
        self.assertEqual([p["pid"] for p in self.cr.owned_by_run(left, r"C:\Temp\cia-audit-abc")], [12])
        self.assertEqual(self.cr.owned_by_run(left, ""), [])                                # no copy, nothing owned

    def test_a_process_seen_in_the_runs_tree_is_owned_only_with_the_same_command(self):
        snap = [{"pid": 50, "ppid": 1, "cmd": "codex exec"},                      # the agent
                {"pid": 51, "ppid": 50, "cmd": "bash npm test"},
                {"pid": 52, "ppid": 51, "cmd": "graphify watch runner"},          # relative path, no copy name
                {"pid": 60, "ppid": 1, "cmd": "graphify watch runner"}]           # a parallel run's twin
        seen = self.cr.descendants(snap, {50})
        self.assertEqual(seen, {51: "bash npm test", 52: "graphify watch runner"})
        left = [{"pid": 52, "ppid": 51, "cmd": "graphify watch runner"},
                {"pid": 60, "ppid": 999, "cmd": "graphify watch runner"},
                {"pid": 51, "ppid": 999, "cmd": "notepad.exe"}]                   # PID 51 reused by something else
        self.assertEqual([p["pid"] for p in self.cr.owned_by_run(left, r"C:\Temp\cia-audit-abc", seen)], [52])

    def test_children_of_a_stopped_leftover_count_as_stopped(self):
        left = [{"pid": 82, "ppid": 64, "cmd": "graphify watch C:/Temp/cia-audit-abc/runner"},
                {"pid": 74, "ppid": 82, "cmd": "python graphify.exe watch"},
                {"pid": 26, "ppid": 74, "cmd": "python graphify.exe watch"},
                {"pid": 99, "ppid": 1, "cmd": "notepad.exe"}]
        self.assertEqual(set(self.cr.descendants(left, {82})), {74, 26})

    def test_run_watched_returns_the_output_and_sees_a_child(self):
        code = "import subprocess,sys,time; c=subprocess.Popen([sys.executable,'-c','import time; time.sleep(8)']); time.sleep(7); print(input())"
        res, seen = self.cr.run_watched([sys.executable, "-c", code], None, "hello\n", 60)
        self.assertEqual((res.returncode, res.stdout.strip()), (0, "hello"))
        self.assertTrue(any("time.sleep(8)" in c for c in seen.values()))

    def test_a_detached_grandchild_whose_parent_exited_is_still_marked_as_the_runs(self):
        # Run C21: pwsh -> python Popen(graphify watch .) -> python exits inside one poll; only the
        # inherited environment still ties the watcher to the run.
        try:
            import psutil
        except ImportError:
            self.skipTest("psutil not installed; marked() is empty by design")
        cwd = tempfile.mkdtemp(prefix="cia-audit-mark-")
        code = ("import subprocess,sys; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],"
                "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(p.pid)")
        res, _ = self.cr.run_watched([sys.executable, "-c", code], cwd, "", 60)
        gc = int(res.stdout.strip())
        try:
            self.assertEqual(self.cr.marked([gc, os.getpid()], cwd), {gc})
            left = [{"pid": gc, "ppid": 99999, "cmd": "python -c sleep"}]
            self.assertEqual(self.cr.owned_by_run(left, cwd, {}, {gc}), left)
        finally:
            psutil.Process(gc).kill()

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


class BuildReportCollectionTests(unittest.TestCase):
    """The build report is a file in the project; the harness collects it and counts its blocks."""

    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import cold_run
        self.cr = cold_run
        self.root = SCRIPT.parents[2]   # the skill under test, whose tools/build_report.py does the count

    def test_missing_file_is_said_not_assumed(self):
        with tempfile.TemporaryDirectory() as d:
            label, body = self.cr.collect_report(Path(d) / self.cr.BUILD_REPORT, self.root, "")
        self.assertEqual(label, "report-file none | ")
        self.assertEqual(body, "")

    def test_file_is_appended_and_counted_by_the_skill_checker(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / self.cr.BUILD_REPORT
            p.write_text("Mode: build mode - save, a.py\n", encoding="utf-8")
            label, body = self.cr.collect_report(p, self.root, "")
        self.assertRegex(label, r"^report-file 1/\d+ \| $")
        self.assertIn("collected from the copy", body)
        self.assertIn("Mode: build mode", body)


    def test_an_audit_report_is_counted_by_the_audit_checker(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / self.cr.AUDIT_REPORT
            p.write_text("ROUTE tools/route.py\n", encoding="utf-8")
            label, _ = self.cr.collect_report(p, self.root, "")
        self.assertRegex(label, r"^report-file \d+/6 \| $")   # audit_report has six parts, build_report 13

    def test_a_cold_run_does_not_load_the_owners_user_settings(self):
        cmd = self.cr.build_command("claude", "p", "sonnet", mode="audit")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project,local")
        egm = self.cr.build_command("claude", "p", "sonnet", mode="egm", reviewer="comprehension")
        self.assertNotIn("--setting-sources", egm)   # the Goldfish reviewer is a user-level plugin agent

    def test_each_skill_names_its_own_audit_report(self):
        self.assertEqual(self.cr.audit_report_name(Path("S:/ai/skills/cia")), self.cr.AUDIT_REPORT)
        self.assertEqual(self.cr.audit_report_name(Path("S:/ai/skills/ecommerce-cia")), "ecommerce-cia-audit-report.md")

    def test_an_audit_may_write_its_report_and_nothing_else(self):
        tools = self.cr.ALLOWED_TOOLS["audit"]
        self.assertIn("Edit(./cia-audit-report.md)", tools)
        self.assertFalse({"Write", "Edit"} & set(tools))

    def test_a_late_notification_does_not_replace_the_report(self):
        # claude -p returns only the last turn; the report is the longest reply in the transcript.
        lines = [json.dumps({"type": "user", "message": {"content": "x" * 9000}}),
                 json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "# Report\n" + "f" * 5000}]}}),
                 "not json",
                 json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "The server stopped."}]}})]
        self.assertTrue(self.cr.longest_reply("\n".join(lines)).startswith("# Report"))
        self.assertEqual(self.cr.longest_reply(""), "")
        self.assertIn("Stop every server you started", self.cr.SHELL_LINE)

    def test_transcript_path_encodes_the_cwd_as_claude_code_does(self):
        p = self.cr.transcript_of("abc", "S:/ai/x y/cia-audit-n8", home="S:/h")
        self.assertEqual(p.name, "abc.jsonl")
        # endswith, not equal: off Windows "S:/..." is a relative path and resolve() puts the cwd in front (CI is Linux).
        self.assertTrue(p.parent.name.endswith("S--ai-x-y-cia-audit-n8"), p.parent.name)

    def test_every_fixture_runtime_can_start_its_own_shop(self):
        # A fixture the run must start itself needs its runtime on the list, and named in the prompt line:
        # php was missing, and two live-fixture runs stopped to ask the owner (2026-11-10).
        for runtime in ("python", "node", "php"):
            self.assertIn(f"Bash({runtime}:*)", self.cr.READ_TOOLS)
            self.assertIn(runtime, self.cr.SHELL_LINE)


if __name__ == "__main__":
    unittest.main()
