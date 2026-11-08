"""Guard tests for tools/score.py: build rows never move the audit gate, and the build gate holds."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import score  # noqa: E402

HDR = "| Date | Skill commit | Runtime | Tier | Hits | Near | Miss | False+ | Minutes | Note |"


def row(date, hits, near=0, miss=0, false=0, runtime="Claude Opus", tier="Screen", commit="abc"):
    return f"| {date} | `{commit}` | {runtime} | {tier} | {hits} | {near} | {miss} | {false} | 5 | n |"


def runs_text(audit, build, runtime_ok=True):
    """Three tables: fixture, runtime, build. The runtime row keeps the audit gate's own
    'every scored run has a runtime row' rule satisfied so tests isolate what they mean to."""
    out = ["# RUNS", "", HDR, *audit, "", "## Runtime evidence, per run (2026-09-24 onward)", "",
           "| Date | Fixture | Ladders | Adversarial rows | Probes | Ledger rows P / F / U | PASS without artefact | Note |"]
    if runtime_ok:
        for d in sorted({r.split("|")[1].strip() for r in audit}):
            out.append(f"| {d} | fixture-service | 1 | 1 | 1 | 1/0/0 | 0 | n |")
    out += ["", "## Build-mode runs (2026-11-09 onward)", "", HDR, *build, ""]
    return "\n".join(out)


class ScoreTests(unittest.TestCase):
    def run_score(self, text, *args):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "RUNS.md"
        p.write_text(text, encoding="utf-8")
        old, score.RUNS = score.RUNS, p
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = score.main(["score.py", *args])
        finally:
            score.RUNS = old
        return code, out.getvalue(), err.getvalue()

    def use(self, text):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "RUNS.md"
        p.write_text(text, encoding="utf-8")
        old, score.RUNS = score.RUNS, p
        self.addCleanup(setattr, score, "RUNS", old)

    AUDIT = [row("2026-11-01", 10), row("2026-11-02", 10)]

    def test_build_row_not_counted_as_audit(self):
        self.use(runs_text(self.AUDIT, [row("2026-11-10", 1, miss=9)]))
        self.assertEqual(len(score.rows()), 2)
        self.assertEqual(len(score.build_rows()), 1)
        self.assertEqual(score.build_rows()[0]["score"], -8)

    def test_build_regression_fails_gate(self):
        t = runs_text(self.AUDIT, [row("2026-11-10", 8), row("2026-11-11", 5, miss=3)])
        code, _, err = self.run_score(t, "--gate")
        self.assertEqual(code, 1)
        self.assertIn("build run", err)

    def test_build_improvement_passes_gate(self):
        t = runs_text(self.AUDIT, [row("2026-11-10", 5), row("2026-11-11", 8)])
        self.assertEqual(self.run_score(t, "--gate")[0], 0)

    def test_empty_or_placeholder_build_table_passes(self):
        ph = "| - | - | - | - | - | - | - | - | - | none yet |"
        for build in ([], [ph]):
            code, out, _ = self.run_score(runs_text(self.AUDIT, build), "--gate")
            self.assertEqual(code, 0)
            self.assertIn("build: no scored build run yet", out)

    def test_no_build_section_passes(self):
        t = runs_text(self.AUDIT, []).split("## Build-mode runs")[0]
        code, out, _ = self.run_score(t, "--gate")
        self.assertEqual(code, 0)
        self.assertIn("build: no scored build run yet", out)

    def test_audit_regression_still_fails(self):
        t = runs_text([row("2026-11-01", 10, commit="aaaaaaa"), row("2026-11-02", 7, miss=3, commit="bbbbbbb")],
                      [row("2026-11-10", 9)])
        self.assertEqual(self.run_score(t, "--gate")[0], 1)

    def gate_on(self, groups):
        """groups: list of (commit, [(hits, near, miss)...]); returns the --gate exit code."""
        audit = [row(f"2026-11-{i + 1:02d}", h, near=n, miss=m, commit=c)
                 for i, (c, runs) in enumerate(groups) for (h, n, m) in runs]
        return self.run_score(runs_text(audit, []), "--gate")[0]

    def test_per_commit_gate(self):
        base = ("aaaaaaa", [(12, 0, 0)])
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(12, 0, 0), (9, 3, 0)])]), 1)   # mean 11.25 < 11.5
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(9, 3, 0), (9, 3, 0)])]), 1)    # mean 10.5
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(11, 1, 0), (11, 1, 0)])]), 0)  # mean 11.5, at the floor
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(12, 0, 0), (11, 0, 0)])]), 0)  # mean 11.5
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(12, 0, 0), (12, 0, 1)])]), 1)  # a miss is never noise
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(12, 0, 0)])]), 1)              # one run is a sample
        reverted = ("ccccccc` (reverted in `ddddddd", [(10, 0, 0), (12, 0, 0)])
        self.assertEqual(self.gate_on([base, ("bbbbbbb", [(11, 1, 0), (11, 1, 0)]), reverted]), 0)  # judged: bbbbbbb

    def test_build_gate_is_a_ratchet(self):
        build = [row("2026-11-10", 8), row("2026-11-11", 2), row("2026-11-12", 5)]
        self.assertEqual(self.run_score(runs_text(self.AUDIT, build), "--gate")[0], 1)

    def test_default_output_has_build_line(self):
        code, out, _ = self.run_score(runs_text(self.AUDIT, [row("2026-11-10", 9)]))
        self.assertEqual(code, 0)
        self.assertIn("build: [opus]", out)


if __name__ == "__main__":
    unittest.main()
