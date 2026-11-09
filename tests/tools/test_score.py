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


def row(date, hits, near=0, miss=0, false=0, runtime="Claude Opus", tier="Screen", commit="abc", note="n"):
    return f"| {date} | `{commit}` | {runtime} | {tier} | {hits} | {near} | {miss} | {false} | 5 | {note} |"


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
        build = [row("2026-11-10", 8, commit="aaaaaaa"), row("2026-11-10", 8, commit="aaaaaaa"),
                 row("2026-11-11", 5, miss=3, commit="bbbbbbb"), row("2026-11-11", 5, miss=3, commit="bbbbbbb")]
        code, _, err = self.run_score(runs_text(self.AUDIT, build), "--gate")
        self.assertEqual(code, 1)
        self.assertIn("BUILD GATE", err)

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

    def test_a_commit_is_gated_on_every_fixture_with_history(self):
        svc, ed = "Screen on **fixture-service**", "Screen on **fixture-editor**"
        base = [row("2026-11-01", 12, commit="aaaaaaa", tier=svc), row("2026-11-01", 12, commit="aaaaaaa", tier=svc),
                row("2026-11-01", 11, commit="aaaaaaa", tier=ed), row("2026-11-01", 11, commit="aaaaaaa", tier=ed)]
        only_one = base + [row("2026-11-02", 11, commit="bbbbbbb", tier=ed), row("2026-11-02", 11, commit="bbbbbbb", tier=ed)]
        self.assertEqual(self.run_score(runs_text(only_one, []), "--gate")[0], 1)   # never run on fixture-service
        both = only_one + [row("2026-11-02", 12, commit="bbbbbbb", tier=svc), row("2026-11-02", 11, commit="bbbbbbb", tier=svc)]
        self.assertEqual(self.run_score(runs_text(both, []), "--gate")[0], 0)
        weak = both[:-1] + [row("2026-11-02", 9, near=1, commit="bbbbbbb", tier=svc)]
        self.assertEqual(self.run_score(runs_text(weak, []), "--gate")[0], 1)       # 10.75 < 11 on one fixture

    def test_a_row_one_run_missed_and_its_pair_found_is_variance_not_doctrine(self):
        base = [row("2026-11-01", 11, commit="aaaaaaa"), row("2026-11-01", 11, commit="aaaaaaa")]
        pair = base + [row("2026-11-02", 12, commit="bbbbbbb"),
                       row("2026-11-02", 11, miss=1, commit="bbbbbbb", note="**11.** missed: E8. rest")]
        self.assertEqual(self.run_score(runs_text(pair, []), "--gate")[0], 0)    # mean 11 >= floor 10.5, E8 found by the pair
        both = base + [row("2026-11-02", 11, miss=1, commit="bbbbbbb", note="missed: E8"),
                       row("2026-11-02", 11, miss=1, commit="bbbbbbb", note="missed: E8, row 3")]
        code, _, err = self.run_score(runs_text(both, []), "--gate")
        self.assertEqual(code, 1)
        self.assertIn("every run missed e8", err)
        untagged = base + [row("2026-11-02", 12, commit="bbbbbbb"), row("2026-11-02", 11, miss=1, commit="bbbbbbb")]
        self.assertEqual(self.run_score(runs_text(untagged, []), "--gate")[0], 1)   # no tag: cannot tell, blocks
        false = base + [row("2026-11-02", 12, commit="bbbbbbb"), row("2026-11-02", 12, false=1, commit="bbbbbbb")]
        self.assertEqual(self.run_score(runs_text(false, []), "--gate")[0], 1)      # a false positive always blocks

    def test_second_stage_is_two_more_runs_once(self):
        base = [row("2026-11-01", 11, commit="aaaaaaa"), row("2026-11-01", 11, commit="aaaaaaa")]   # floor 10.5
        two = base + [row("2026-11-02", 10, commit="bbbbbbb"), row("2026-11-02", 10, near=1, commit="bbbbbbb")]
        code, _, err = self.run_score(runs_text(two, []), "--gate")
        self.assertEqual(code, 1)
        self.assertIn("Within one row", err)                                       # 10.25: earns a second stage
        four = two + [row("2026-11-03", 11, commit="bbbbbbb"), row("2026-11-03", 11, commit="bbbbbbb")]
        self.assertEqual(self.run_score(runs_text(four, []), "--gate")[0], 0)      # 10.625 >= 10.5 over four
        three = two + [row("2026-11-03", 12, commit="bbbbbbb")]
        self.assertEqual(self.run_score(runs_text(three, []), "--gate")[0], 1)     # three is neither stage
        six = four + [row("2026-11-04", 12, commit="bbbbbbb"), row("2026-11-04", 12, commit="bbbbbbb")]
        self.assertEqual(self.run_score(runs_text(six, []), "--gate")[0], 1)       # no third stage
        far = base + [row("2026-11-02", 9, commit="bbbbbbb"), row("2026-11-02", 9, commit="bbbbbbb")]
        self.assertNotIn("Within one row", self.run_score(runs_text(far, []), "--gate")[2])

    def test_floor_follows_recent_median_and_cannot_drift_more_than_a_row(self):
        lucky = [("aaaaaaa", [(12, 0, 0), (12, 0, 0)])] + [(c * 7, [(11, 1, 0), (11, 1, 0)]) for c in "bcde"]
        self.assertEqual(self.gate_on(lucky + [("fffffff", [(11, 1, 0), (11, 0, 0)])]), 0)  # 11.25 >= median 11.5 - 0.5
        self.assertEqual(self.gate_on(lucky + [("fffffff", [(11, 0, 0), (10, 1, 0)])]), 1)  # 10.75 < 11
        drift = [("aaaaaaa", [(12, 0, 0), (12, 0, 0)])] + [(c * 7, [(10, 1, 0), (10, 1, 0)]) for c in "bcde"]
        self.assertEqual(self.gate_on(drift + [("fffffff", [(10, 1, 0), (10, 1, 0)])]), 1)  # 10.5 < best 12 - DRIFT

    def test_resolved_model_pools_apart_from_its_alias(self):
        # An alias row cannot be compared with a row that names what answered; a resolved id can.
        self.assertEqual(score.model_of("Claude Sonnet (harness; resolved claude-sonnet-5-5, $1)"), "claude-sonnet-5-5")
        self.assertEqual(score.model_of("Claude Sonnet (harness)"), "sonnet")
        self.assertTrue(score.is_cheap("claude-sonnet-5-5"))   # as cheap as its alias
        self.assertFalse(score.is_cheap("opus"))
        res = "Claude Sonnet (harness; resolved claude-sonnet-5-5)"
        audit = [row("2026-11-01", 12, commit="aaaaaaa", runtime="Claude Sonnet"),
                 row("2026-11-01", 12, commit="aaaaaaa", runtime="Claude Sonnet"),
                 row("2026-11-02", 7, near=1, miss=1, commit="bbbbbbb", runtime=res),
                 row("2026-11-02", 7, near=1, miss=1, commit="bbbbbbb", runtime=res),
                 row("2026-11-03", 10, near=2, commit="ccccccc", runtime=res),
                 row("2026-11-03", 10, near=1, commit="ccccccc", runtime=res)]
        self.assertEqual(self.run_score(runs_text(audit, []), "--gate")[0], 0)   # 10.75 vs 7.5 on one model
        audit[-1] = row("2026-11-03", 10, near=1, miss=1, commit="ccccccc", runtime=res)
        self.assertEqual(self.run_score(runs_text(audit, []), "--gate")[0], 1)   # a miss still blocks
        first = audit[:2] + [row("2026-11-02", 11, miss=1, commit="bbbbbbb", runtime=res)]
        self.assertEqual(self.run_score(runs_text(first, []), "--gate")[0], 1)   # even on a model's first commit

    def test_other_runtimes_section_is_not_a_gate_input(self):
        # A runtime's first measurement cannot be a regression; its rows live after the build table.
        other = "\n## Other runtimes (2026-11-09 onward)\n\n" + HDR + "\n" + row("2026-11-12", 0, near=10, miss=2, runtime="Codex") + "\n"
        t = runs_text(self.AUDIT, [row("2026-11-10", 5), row("2026-11-11", 8)]) + other
        self.use(t)
        self.assertEqual(len(score.rows()), 2)
        self.assertEqual(len(score.build_rows()), 2)
        self.assertEqual(self.run_score(t, "--gate")[0], 0)

    def test_codex_rows_have_their_own_gate(self):
        svc = "Screen on **fixture-service**"
        cx = lambda h, n=0, m=0, c="aaaaaaa", note="n": row("2026-11-12", h, near=n, miss=m, runtime="**Codex**",  # noqa: E731
                                                          tier=svc, commit=c, note=note)
        other = lambda rows: "\n## Other runtimes (2026-11-09 onward)\n\n" + HDR + "\n" + "\n".join(rows) + "\n"  # noqa: E731
        base = runs_text(self.AUDIT, [])
        history = [cx(10, m=1, note="missed: row 8"), cx(9, m=1, note="missed: row 10")]   # floor: 9.5-0.5, best-1
        self.use(base + other(history))
        self.assertEqual(len(score.codex_rows()), 2)
        self.assertEqual(len(score.rows()), 2)                                                # never pooled with Claude
        self.assertEqual(self.run_score(base + other(history + [cx(11, 1, c="bbbbbbb"), cx(11, 1, c="bbbbbbb")]),
                                        "--gate")[0], 0)                                     # 11.5 clears its floor
        code, _, err = self.run_score(base + other(history + [cx(7, m=2, c="bbbbbbb"), cx(7, m=2, c="bbbbbbb")]),
                                      "--gate")
        self.assertEqual(code, 1)
        self.assertIn("CODEX GATE", err)                                                     # 5 < floor 9
        clean = history + [cx(11, 1, c="bbbbbbb"), cx(11, 1, c="bbbbbbb")]
        both = clean + [cx(11, m=1, c="ccccccc", note="missed: row 12"), cx(11, m=1, c="ccccccc", note="missed: row 12")]
        self.assertEqual(self.run_score(base + other(both), "--gate")[0], 1)                 # a shared miss is doctrine
        # A run at another reasoning effort is its own series: its first pair is a baseline, and it
        # neither joins nor resets the default-effort series' floor.
        hi = lambda h, m=0: row("2026-11-13", h, miss=m, runtime="**Codex** (`--effort high`)", tier=svc,  # noqa: E731
                                commit="bbbbbbb", note="missed: row 5" if m else "n")
        self.assertEqual(score.model_of("**Codex** (as above, `--effort high`, audit run C22)"), "codex-high")
        code, out, _ = self.run_score(base + other(clean + [hi(12), hi(11, m=1)]), "--gate")
        self.assertEqual(code, 0)
        self.assertIn("codex gate [codex-high]", out)
        self.assertIn("codex gate [codex]", out)

    def build_gate_on(self, groups):
        """groups: list of (commit, [scores...]) as clean build runs; returns the --gate exit code."""
        build = [row(f"2026-11-{i + 10:02d}", s, commit=c) for i, (c, ss) in enumerate(groups) for s in ss]
        return self.run_score(runs_text(self.AUDIT, build), "--gate")[0]

    def test_build_gate_is_the_per_commit_mean(self):
        self.assertEqual(self.build_gate_on([("aaaaaaa", [8, 8]), ("bbbbbbb", [2, 5])]), 1)   # 3.5 < 7.5
        self.assertEqual(self.build_gate_on([("aaaaaaa", [8, 8]), ("bbbbbbb", [8])]), 1)      # one run is a sample
        self.assertEqual(self.build_gate_on([("aaaaaaa", [8, 8]), ("bbbbbbb", [8, 7])]), 0)   # 7.5, at the floor
        # One lucky row no longer sets the bar: 10 sits in a commit whose mean is 7.
        lucky = [("aaaaaaa", [5, 5]), ("bbbbbbb", [10, 4]), ("ccccccc", [8, 5])]
        self.assertEqual(self.build_gate_on(lucky), 0)                                     # 6.5 >= floor 6

    def test_a_later_clean_run_on_reverted_doctrine_does_not_block_the_shipped_commit(self):
        build = [row("2026-11-10", 5, miss=3, commit="aaaaaaa"), row("2026-11-10", 5, miss=3, commit="aaaaaaa"),
                 row("2026-11-11", 9, commit="bbbbbbb` (reverted in `ccccccc"),
                 row("2026-11-11", 2, miss=6, commit="bbbbbbb` (reverted in `ccccccc")]
        self.assertEqual(self.run_score(runs_text(self.AUDIT, build), "--gate")[0], 0)
        build += [row("2026-11-12", 9, commit="ddddddd"), row("2026-11-12", 8, miss=1, commit="ddddddd")]
        self.assertEqual(self.run_score(runs_text(self.AUDIT, build), "--gate")[0], 1)  # after a clean run: a miss blocks

    def test_a_later_reverted_experiment_does_not_raise_the_shipped_floor(self):
        build = [row("2026-11-10", 3, commit="aaaaaaa"), row("2026-11-10", 3, commit="aaaaaaa"),
                 row("2026-11-11", 9, commit="bbbbbbb` (reverted in `ccccccc"),
                 row("2026-11-11", 9, commit="bbbbbbb` (reverted in `ccccccc")]
        self.assertEqual(self.run_score(runs_text(self.AUDIT, build), "--gate")[0], 0)   # 3 is judged on its past

    def test_build_gate_skips_reverted_rows(self):
        build = [row("2026-11-10", 4), row("2026-11-11", 4), row("2026-11-12", 2, commit="aaaaaaa` (reverted in `bbbbbbb")]
        self.assertEqual(self.run_score(runs_text(self.AUDIT, build), "--gate")[0], 0)
        build[-1] = row("2026-11-12", 2, commit="aaaaaaa")
        self.assertEqual(self.run_score(runs_text(self.AUDIT, build), "--gate")[0], 1)

    def test_corpus_rate_is_the_newest_verdict_per_entry(self):
        rows = [{"date": "2026-09-24", "entry": "a", "verdict": "MISS"}, {"date": "2026-11-10", "entry": "a", "verdict": "HIT"},
                {"date": "2026-09-24", "entry": "b", "verdict": "PARTIAL"}, {"date": "2026-11-10", "entry": "b", "verdict": "N/A"},
                {"date": "2026-11-10", "entry": "c", "verdict": "MISS"}]
        cur = {r["entry"]: r["verdict"] for r in score.corpus_current(rows)}
        self.assertEqual(cur, {"a": "HIT", "b": "PARTIAL", "c": "MISS"})   # N/A keeps the last real measurement

    def test_default_output_has_build_line(self):
        code, out, _ = self.run_score(runs_text(self.AUDIT, [row("2026-11-10", 9)]))
        self.assertEqual(code, 0)
        self.assertIn("build: [opus]", out)


if __name__ == "__main__":
    unittest.main()
