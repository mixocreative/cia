"""Guard tests for tools/design_check.py. Each check is shown to FAIL on a planted defect and PASS on a clean case.

A check that has never printed a finding is untested (S21: a passing assertion that something is empty proves
nothing until something proves it can be non-empty). So every rule has one planted failure below.

Run: python -m unittest discover -s tests/design-check -t tests/design-check
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HERE / "tools"))
import design_check as dc  # noqa: E402


def run(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args)
    return code, buf.getvalue()


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class DepsTests(unittest.TestCase):
    def test_clean_python_passes(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            write(r, "app/__init__.py", "")
            write(r, "app/core.py", "import os\n")
            write(r, "app/web.py", "from app import core\n")
            code, out = run(dc.cmd_deps, r, None)
            self.assertEqual(code, 0, out)
            self.assertIn("cycles 0", out)

    def test_planted_python_cycle_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            write(r, "app/__init__.py", "")
            write(r, "app/a.py", "from app import b\n")
            write(r, "app/b.py", "from app import a\n")
            code, out = run(dc.cmd_deps, r, None)
            self.assertEqual(code, 1, out)
            self.assertIn("CYCLE", out)

    def test_planted_upward_layer_import_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            write(r, "src/features/cart/ui.ts", "import { x } from '../../pages/home/view';\n")
            write(r, "src/pages/home/view.ts", "export const x = 1;\n")
            rules = r / "design-rules.json"
            rules.write_text(json.dumps({
                "source_roots": ["src"],
                "layers": {"order": ["app", "pages", "widgets", "features", "entities", "shared"],
                           "same_layer_slices": "forbidden"},
            }), encoding="utf-8")
            code, out = run(dc.cmd_deps, r, rules)
            self.assertEqual(code, 1, out)
            self.assertIn("upward import", out)

    def test_exception_without_owner_is_config_error(self):
        with tempfile.TemporaryDirectory() as d:
            rules = Path(d) / "rules.json"
            rules.write_text(json.dumps({"exceptions": [{"from": "a/*", "to": "b/*", "reason": "x"}]}), encoding="utf-8")
            with self.assertRaises(dc.ConfigError):
                dc.load_rules(rules)

    def test_exception_with_reason_and_owner_is_honoured(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            write(r, "src/features/cart/ui.ts", "import { x } from '../../pages/home/view';\n")
            write(r, "src/pages/home/view.ts", "export const x = 1;\n")
            rules = r / "design-rules.json"
            rules.write_text(json.dumps({
                "source_roots": ["src"],
                "layers": {"order": ["app", "pages", "widgets", "features", "entities", "shared"]},
                "exceptions": [{"from": "features/cart/*", "to": "pages/home/*",
                                "reason": "legacy link, tracked", "owner": "cart team"}],
            }), encoding="utf-8")
            code, out = run(dc.cmd_deps, r, rules)
            self.assertEqual(code, 0, out)
            self.assertIn("exceptions honoured 1", out)


class AdrTests(unittest.TestCase):
    GOOD = ("# 0001 — Use Postgres\nStatus: accepted\nDate: 2026-11-09\nContext: need transactions\n"
            "Decision: Postgres for the queue\nConsequences: one more service to run\n")

    def test_clean_adr_passes(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), "0001-use-postgres.md", self.GOOD)
            code, out = run(dc.cmd_adr, Path(d))
            self.assertEqual(code, 0, out)

    def test_planted_missing_consequences_fails(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), "0001-use-postgres.md", self.GOOD.replace("Consequences: one more service to run\n", ""))
            code, out = run(dc.cmd_adr, Path(d))
            self.assertEqual(code, 1, out)
            self.assertIn("MISSING Consequences", out)

    def test_planted_dangling_supersede_fails(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), "0002-use-redis.md", self.GOOD.replace("accepted", "superseded by 0009"))
            code, out = run(dc.cmd_adr, Path(d))
            self.assertEqual(code, 1, out)
            self.assertIn("SUPERSEDES", out)


class StatesTests(unittest.TestCase):
    def table(self, **over):
        t = {
            "initial": "idle",
            "states": ["idle", "submitting", "done", "failed"],
            "events": ["submit", "ok", "error"],
            "terminal": ["done"],
            "transitions": {
                "idle": {"submit": "submitting", "ok": {"ignore": "nothing to ack"}, "error": {"ignore": "not submitting"}},
                "submitting": {"submit": {"ignore": "double submit guarded"}, "ok": "done", "error": "failed"},
                "failed": {"submit": "submitting", "ok": {"ignore": "no pending"}, "error": {"ignore": "already failed"}},
                "done": {"submit": {"ignore": "terminal"}, "ok": {"ignore": "terminal"}, "error": {"ignore": "terminal"}},
            },
        }
        t.update(over)
        return t

    def check(self, t):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "table.json"
            p.write_text(json.dumps(t), encoding="utf-8")
            return run(dc.cmd_states, p)

    def test_complete_table_passes(self):
        code, out = self.check(self.table())
        self.assertEqual(code, 0, out)

    def test_planted_missing_cell_fails(self):
        t = self.table()
        del t["transitions"]["submitting"]["error"]
        code, out = self.check(t)
        self.assertEqual(code, 1, out)
        self.assertIn("MISSING submitting x error", out)

    def test_planted_unreachable_state_fails(self):
        t = self.table(states=["idle", "submitting", "done", "failed", "orphan"])
        t["transitions"]["orphan"] = {e: {"ignore": "unreached"} for e in t["events"]}
        code, out = self.check(t)
        self.assertEqual(code, 1, out)
        self.assertIn("UNREACHABLE orphan", out)

    def test_planted_exitless_state_fails(self):
        t = self.table()
        t["transitions"]["failed"] = {e: {"ignore": "stuck"} for e in t["events"]}
        code, out = self.check(t)
        self.assertEqual(code, 1, out)
        self.assertIn("EXITLESS failed", out)


if __name__ == "__main__":
    unittest.main()
