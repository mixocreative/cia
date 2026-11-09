"""Guard tests for tools/audit_report.py: receipts are checked against the references, leads and inventory answered."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_report as ar  # noqa: E402
from receipts import scan  # noqa: E402

FOUND, _ = scan()
PHRASE = {("sweeps/" if k.startswith("sweeps/") else k): v for k, v in FOUND.items()}


def report(receipts=ar.ALWAYS + ar.WITH_SURFACE, extra=""):
    quoted = " | ".join(f'{r} "{PHRASE[r]}"' for r in receipts)
    sweeps = "\n".join(f"- S{n}: swept" for n in range(1, 25))
    lines = "\n".join(f"{n}. line" for n in range(1, 15))
    return (f"ROUTE tools/route.py 1\nSURFACE page=1 · cli=0 · http routes=0\n"
            f"LEADS (tools/sweep_leads.py, X0) - leads\nS13 no caller in tree: app/a.py:4 `orphan`\n"
            f"boundary: x\n\nF1 HIGH S13 `app/a.py:4` orphan has no caller\n{sweeps}\n{lines}\n"
            f"Reference receipts: {quoted}\n{extra}")


def missing(text):
    return [name for name, ok, _ in ar.checks(text) if not ok]


class AuditReportTests(unittest.TestCase):
    def test_complete_report_passes(self):
        self.assertEqual(missing(report()), [])

    def test_a_skipped_reference_is_named(self):
        text = report(receipts=tuple(r for r in ar.ALWAYS if r != "evidence.md") + ar.WITH_SURFACE)
        self.assertIn("receipts", missing(text))
        hint = next(h for n, ok, h in ar.checks(text) if n == "receipts")
        self.assertIn("evidence.md", hint)

    def test_a_guessed_receipt_does_not_pass(self):
        text = report().replace(PHRASE["theory.md"], "a codebase has several systems")
        self.assertIn("receipts", missing(text))

    def test_maps_are_not_required_when_the_block_shows_no_surface(self):
        text = report(receipts=ar.ALWAYS).replace("page=1", "page=0")
        self.assertEqual(missing(text), [])
        self.assertIn("receipts", missing(report(receipts=ar.ALWAYS)))   # a page makes them required

    def test_an_unanswered_lead_is_named(self):
        text = report().replace("F1 HIGH S13 `app/a.py:4` orphan has no caller", "")
        self.assertIn("every lead answered", missing(text))

    def test_missing_sweep_and_step_lines(self):
        self.assertIn("sweep lines S1-S24", missing(report().replace("- S17: swept", "")))
        self.assertIn("Step 6 lines 1-14", missing(report().replace("\n7. line", "")))

    def test_inventory_items_need_a_disposition_when_the_block_is_present(self):
        inv = ("INVENTORY (tools/inventory.py, X0) - 2 items\ndef    app/a.py:4  `orphan`\n"
               "test   tests/t.py:1  `test_x`\n\n")
        self.assertIn("every inventory item answered", missing(report(extra=inv)))
        self.assertEqual(missing(report(extra=inv + "tests/t.py:1 read, nothing\n")), [])


if __name__ == "__main__":
    unittest.main()
