"""Guard tests for tools/build_report.py: a complete §3a report passes, each missing block is named."""
import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import build_report as br  # noqa: E402

# A generic document-save build, deliberately not the fixture's job claim: the checker must hold
# for any primary-path write, so its test must not be shaped like the one fixture it is run on.
COMPLETE = '''Mode: build mode - document save, editor/store.py

| ID | Promise | Intent source | Case kinds | Authority needed | Owner |
| doc.save.atomic@1 | a save writes all or nothing | "make save crash-safe" | concurrent, fault-after-first-write, duplicate, refused | A2 | editor/store.py:save |

Primary quantity and observers: the saved document - observed by the file, the recent list

Proofs, red before the code: atomic | race-free | idempotent | loud
FAIL: test_doc_save_atomic_1_atomic
FAIL: test_doc_save_atomic_1_race_free
ERROR: test_doc_save_atomic_1_idempotent
FAIL: test_doc_save_atomic_1_loud

Proofs, green after the code:
Ran 4 tests in 0.1s
OK

| save | PASS | A2 / A2 | proof output above | write, loser refused, duplicate unchanged, fault rolled back |

Closure gates: CG1 4 · CG2 0 · CG3 0 · CG4 0 · CG5 0 · CG6 0 · CG7 1 · CG8 n/a · CG9 n/a · CG10 n/a · CG11 n/a · CG12 n/a · CG13 n/a

Step 6 line 14: SURFACE n/a · JOURNEY n/a · DESIGN n/a · GRAPH n/a · EXECUTORS n/a · TESTS 4 · COMPANIONS none

Debt not taken: none · Reference receipts: "..."
'''


def missing(text):
    return [name for name, ok, _ in br.checks(text) if not ok]


class BuildReportTests(unittest.TestCase):
    def test_complete_report_passes(self):
        self.assertEqual(missing(COMPLETE), [])

    def test_each_block_is_named_when_absent(self):
        cases = {
            "mode": COMPLETE.replace("Mode: build mode", "Doing"),
            "obligation id": COMPLETE.replace("doc.save.atomic@1", "OBL-1").replace("doc_save_atomic_1", "x"),
            "obligation fields": COMPLETE.replace("fault-after-first-write, ", ""),
            "primary quantity": COMPLETE.replace("Primary quantity", "Quantity"),
            "proofs named": COMPLETE.replace("idempotent", "repeat"),   # test names count as naming it
            "red output pasted": COMPLETE.replace("FAIL:", "fail").replace("ERROR:", "err"),
            "green output pasted": COMPLETE.replace("\nOK\n", "\n"),
            "test names carry the id": COMPLETE.replace("test_doc_save_atomic_1_loud", "test_loud"),
            "ledger row": COMPLETE.replace("A2 / A2", "A2"),
            "closure gates": COMPLETE.replace("CG13", "CG"),
            "line 14": COMPLETE.replace("COMPANIONS", "COMP"),
            "debt not taken": COMPLETE.replace("Debt not taken: none · ", ""),
            "receipts": COMPLETE.replace("Reference receipts", "Refs"),
        }
        for block, text in cases.items():
            with self.subTest(block=block):
                self.assertIn(block, missing(text))

    def test_prose_summary_fails_most_blocks(self):
        # The measured failure: correct code, then a summary instead of the form.
        prose = "Done. The claim is now race-free; all 12 tests pass."
        self.assertGreaterEqual(len(missing(prose)), 12)

    def test_form_is_the_one_copy_in_build_standard(self):
        form = br.form_text(br.STANDARD.read_text(encoding="utf-8"))
        self.assertTrue(form.startswith("Mode: build mode"))
        self.assertIn("Closure gates", form)

    def test_cli_exit_codes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(br.main(["form"]), 0)
        self.assertIn("Evidence ledger row", out.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(br.main([]), 2)


if __name__ == "__main__":
    unittest.main()
