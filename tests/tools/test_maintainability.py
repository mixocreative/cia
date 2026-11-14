"""Guard tests for `tools/maintainability.py`, the instrument behind the maintainability doctrine.

WHY THIS FILE EXISTS, and it is not "coverage". On 2026-11-14 this tool shipped with no tests at
all, and SIX false positives were then found in it ONE AT A TIME, by hand, over a working day:

  * M1 exempted a folder by its NAME, so `src/core/assets` (code about assets) was waved through
  * M3 read a three-line window, so a job line on line four read as absent
  * M3 fired on every small file before it had a line threshold
  * M3 did not recognise a Python docstring as prose
  * M4 judged docs the APP imports as content, whose links resolve against the built output
  * M2 matched the BASENAME, so any doc saying "mod.rs" excused every `mod.rs` in the repo

Each was found by chance rather than by a gate, and each one made the tool report a defect that
was not there -- the mirror image of S20's blind instrument, and just as expensive, because a
reader who chases a phantom stops trusting the real rows. Every test below pins one of those
behaviours, so the next regression is a red line rather than another day of hand-auditing.

The owner's objection on 2026-11-14 was that issues kept being found "non stop as if there's no
end to finalize it". The cause was an untested instrument; this file is the end of that loop.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.normpath(os.path.join(HERE, "..", "..", "tools", "maintainability.py"))


def run(root, *extra):
    """The tool as a stranger runs it: a subprocess, so argv parsing and exit codes are real."""
    proc = subprocess.run([sys.executable, TOOL, root, *extra],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def gaps_for(root, rule):
    code, out = run(root, "--json")
    payload = json.loads(out)
    assert payload["gaps"] is not None, "gaps must be null only when enumeration failed"
    return [g for g in payload["gaps"] if g["rule"] == rule], code


class Tree:
    """A throwaway directory. NOT a git worktree, which exercises the filesystem-walk path."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="cia-maint-")
        return self

    def __exit__(self, *exc):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, rel, text):
        full = os.path.join(self.dir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return full

    def code(self, rel, lines, head=""):
        """A code file of `lines` non-trivial lines, optionally led by `head` prose."""
        body = "\n".join("const x%d = %d;" % (i, i) for i in range(lines))
        self.write(rel, (head + "\n" if head else "") + body + "\n")


class M1FolderMaps(unittest.TestCase):
    def test_folder_past_the_limit_needs_a_readme(self):
        with Tree() as t:
            for i in range(25):
                t.code("src/wide/f%d.ts" % i, 3)
            found, _ = gaps_for(t.dir, "M1")
            self.assertEqual(["src/wide"], [g["path"] for g in found])

    def test_a_readme_answers_it(self):
        with Tree() as t:
            for i in range(25):
                t.code("src/wide/f%d.ts" % i, 3)
            t.write("src/wide/README.md", "# map\n")
            found, _ = gaps_for(t.dir, "M1")
            self.assertEqual([], found)

    def test_the_exemption_tests_contents_not_the_folder_name(self):
        """THE FIRST FALSE POSITIVE. Keyed on the name, `assets` was exempt though it held code."""
        with Tree() as t:
            for i in range(25):
                t.code("src/core/assets/f%d.ts" % i, 3)       # code ABOUT assets: needs a map
            for i in range(25):
                t.write("store/pics/p%d.png" % i, "x")        # real data: exempt by contents
            found, _ = gaps_for(t.dir, "M1")
            paths = [g["path"] for g in found]
            self.assertIn("src/core/assets", paths)
            self.assertNotIn("store/pics", paths)


class M2SizeDebt(unittest.TestCase):
    def test_over_the_debt_limit_and_unnamed_is_a_gap(self):
        with Tree() as t:
            t.code("src/big.ts", 700)
            found, _ = gaps_for(t.dir, "M2")
            self.assertEqual(1, len(found))
            self.assertIn("not named as debt", found[0]["detail"])

    def test_naming_it_answers_the_debt_limit(self):
        with Tree() as t:
            t.code("src/big.ts", 700)
            t.write("docs/size-debt.md", "`src/big.ts` is debt; next cut: split the parser.\n")
            found, _ = gaps_for(t.dir, "M2")
            self.assertEqual([], found)

    def test_past_the_cut_limit_naming_is_NOT_enough(self):
        """Rule 5: past 1,000 lines the cut is TAKEN, not written down.

        This is what the tool's own title used to misdescribe as "no doc mentions", sending a
        reader hunting for a missing doc entry that was never the finding.
        """
        with Tree() as t:
            t.code("src/huge.ts", 1200)
            t.write("docs/size-debt.md", "`src/huge.ts` is debt; next cut: later.\n")
            found, _ = gaps_for(t.dir, "M2")
            self.assertEqual(1, len(found))
            self.assertIn("over the 1000 cut limit", found[0]["detail"])
            self.assertNotIn("not named as debt", found[0]["detail"])

    def test_a_bare_basename_elsewhere_does_not_excuse_a_file(self):
        """THE BASENAME HOLE: one doc saying "mod.rs" excused every `mod.rs` in the repo."""
        with Tree() as t:
            t.code("src/supports/plan/mod.rs", 700)
            t.write("docs/notes.md", "Some unrelated prose mentioning mod.rs in passing.\n")
            found, _ = gaps_for(t.dir, "M2")
            self.assertEqual(1, len(found), "a bare basename must not count as named")

    def test_the_last_two_segments_are_accepted_as_shorthand(self):
        with Tree() as t:
            t.code("src/supports/plan/mod.rs", 700)
            t.write("docs/notes.md", "`plan/mod.rs` is debt; next cut: split the solver.\n")
            found, _ = gaps_for(t.dir, "M2")
            self.assertEqual([], found)


class M3JobLine(unittest.TestCase):
    def test_a_long_module_with_no_prose_is_a_gap(self):
        with Tree() as t:
            t.code("src/long.ts", 300)
            found, _ = gaps_for(t.dir, "M3")
            self.assertEqual(["src/long.ts"], [g["path"] for g in found])

    def test_a_short_module_needs_no_job_line(self):
        """It once fired on every small file, which is noise, not a finding."""
        with Tree() as t:
            t.code("src/short.ts", 50)
            found, _ = gaps_for(t.dir, "M3")
            self.assertEqual([], found)

    def test_prose_below_the_old_three_line_window_still_counts(self):
        with Tree() as t:
            t.code("src/long.ts", 300, head="\n\nimport a from 'a';\nimport b from 'b';\n"
                                            "\n// This module turns a plan into placed supports.")
            found, _ = gaps_for(t.dir, "M3")
            self.assertEqual([], found, "a job line past line three must still be seen")

    def test_a_python_docstring_is_prose(self):
        with Tree() as t:
            body = "\n".join("x%d = %d" % (i, i) for i in range(300))
            t.write("src/long.py", '"""Turns a plan into placed supports."""\n' + body + "\n")
            found, _ = gaps_for(t.dir, "M3")
            self.assertEqual([], found)

    def test_barrel_and_test_files_are_exempt(self):
        with Tree() as t:
            t.code("src/index.ts", 300)
            t.code("src/thing.test.ts", 300)
            found, _ = gaps_for(t.dir, "M3")
            self.assertEqual([], found)


class M4LivingLinks(unittest.TestCase):
    def test_a_broken_link_in_a_living_doc_is_a_gap(self):
        with Tree() as t:
            t.code("src/a.ts", 5)
            t.write("docs/guide.md", "See [the plan](./missing.md).\n")
            found, _ = gaps_for(t.dir, "M4")
            self.assertEqual(1, len(found))

    def test_a_resolving_link_is_not(self):
        with Tree() as t:
            t.write("docs/guide.md", "See [the plan](./plan.md).\n")
            t.write("docs/plan.md", "# plan\n")
            found, _ = gaps_for(t.dir, "M4")
            self.assertEqual([], found)

    def test_a_doc_the_app_imports_as_content_is_not_judged(self):
        """M4's first false positive: TERMS.md links into the BUILT output, not the repo."""
        with Tree() as t:
            t.write("src/app.ts", "import terms from '../TERMS.md?raw';\nexport default terms;\n")
            t.write("TERMS.md", "See [the licence](/licence.html).\n")
            found, _ = gaps_for(t.dir, "M4")
            self.assertEqual([], found)

    def test_a_dated_doc_is_a_record_and_is_skipped(self):
        with Tree() as t:
            t.code("src/a.ts", 5)
            t.write("docs/2026-11-14-review.md", "See [gone](./gone.md).\n")
            found, _ = gaps_for(t.dir, "M4")
            self.assertEqual([], found)


class EnumerationAndContract(unittest.TestCase):
    def test_help_exits_zero(self):
        """`--help` returned exit 2 for as long as the tool existed: a stranger's first command."""
        for flag in ("-h", "--help"):
            proc = subprocess.run([sys.executable, TOOL, flag], capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, "%s must succeed" % flag)
            self.assertIn("M1", proc.stdout)

    def test_a_non_git_directory_is_measured_not_refused(self):
        """Codex's finding: it could not measure a fixture copy or an unpacked archive."""
        with Tree() as t:
            t.code("src/big.ts", 700)
            code, out = run(t.dir, "--json")
            payload = json.loads(out)
            self.assertIsNotNone(payload["gaps"])
            self.assertIn("walk", payload["source"])
            # The scope is REPORTED rather than silently assumed: outside a worktree no ignore
            # rules were applied, and Codex's second finding was that marking the
            # ignore-sensitive rules UNVERIFIED instead is incoherent, because M4 can falsely
            # PASS when a link points at an ignored file. So state the scope, never parse
            # `.gitignore`.
            self.assertFalse(payload["ignore_rules_applied"])

    def test_an_empty_directory_is_exit_2_and_never_clean(self):
        """"Nothing to measure" must not read as "nothing wrong" -- gaps is null, not []."""
        with Tree() as t:
            code, out = run(t.dir, "--json")
            self.assertEqual(2, code, "enumeration failure is exit 2, not 0 and not 1")
            self.assertIsNone(json.loads(out)["gaps"])

    def test_a_clean_tree_is_exit_zero(self):
        with Tree() as t:
            t.code("src/fine.ts", 10)
            code, _ = run(t.dir)
            self.assertEqual(0, code)

    def test_gaps_are_exit_one(self):
        with Tree() as t:
            t.code("src/big.ts", 700)
            code, _ = run(t.dir)
            self.assertEqual(1, code)

    def test_the_report_never_claims_the_unmeasurable_rules_are_clean(self):
        """S20: a tool that prints a clean line for what it cannot see is a blind instrument."""
        with Tree() as t:
            t.code("src/fine.ts", 10)
            _, out = run(t.dir)
            self.assertIn("not claimed clean", out)
            self.assertIn("extract jobs, not hubs", out)


if __name__ == "__main__":
    unittest.main()
