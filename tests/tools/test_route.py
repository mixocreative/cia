"""Guard tests for tools/route.py: each rule is planted in a temp tree and must fail if the rule breaks."""
import contextlib
import hashlib
import io
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import route  # noqa: E402


class Tree:
    """A planted project in a temp dir plus an empty fake HOME, so the real machine never leaks in."""

    def __init__(self, test, files):
        self._d = tempfile.TemporaryDirectory()
        test.addCleanup(self._d.cleanup)
        self.root = Path(self._d.name) / "proj"
        self.home = Path(self._d.name) / "home"
        self.home.mkdir()
        self.root.mkdir()
        for rel, text in files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def run(self, *flags, home=None):
        env = {"HOME": str(home or self.home), "USERPROFILE": str(home or self.home)}
        out = io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out):
            code = route.main([str(self.root), "--no-timing", *flags])
        self.code = code
        return out.getvalue()


def line_of(out, key):
    return next(x for x in out.splitlines() if x.startswith(key))


class SurfaceTests(unittest.TestCase):
    def test_page_needs_html_in_a_string(self):
        t = Tree(self, {"a.py": 'X = "<table>"\n'})
        self.assertIn("page=1 (a.py:1 `<table>`", t.run())
        t = Tree(self, {"a.py": 'X = "plain"\n'})
        self.assertIn("page=0", t.run())

    def test_cli_signals(self):
        self.assertIn("cli=1", Tree(self, {"a.py": 'import sys\nif __name__ == "__main__":\n    print(sys.argv)\n'}).run())
        self.assertIn("cli=1", Tree(self, {"a.py": "import argparse\n"}).run())
        self.assertIn("cli=0", Tree(self, {"a.py": "import sys\nx = 1\n"}).run())
        # A plain Node script: the entry guard plus argv, no CLI framework (fixture-editor, 2026-11-09).
        js = "if (require.main === module) {\n  run(process.argv.slice(2));\n}\n"
        self.assertIn("cli=1 (a.js:2 `process.argv`)", Tree(self, {"a.js": js}).run())
        self.assertIn("cli=0", Tree(self, {"a.js": "const x = process.argv;\n"}).run())  # argv alone is no entry

    def test_form_target_resolved_only_when_a_route_exists(self):
        form = "H = \"<form formaction='/x'>\"\n"
        out = Tree(self, {"a.py": form}).run()
        self.assertRegex(out, r"form targets=1 \(a\.py:1 .*no handler in tree")
        out = Tree(self, {"a.py": form, "b.py": "@app.route('/x')\ndef x(): pass\n"}).run()
        self.assertIn("http routes=1", out)
        self.assertIn("form targets=1", out)
        self.assertNotIn("no handler in tree", out)

    def test_parametrised_target_matches_param_route(self):
        out = Tree(self, {"a.py": "H = \"<form action='/jobs/%d/retry'>\"\n",
                          "b.py": "@app.post('/jobs/<int:id>/retry')\ndef f(): pass\n"}).run()
        self.assertNotIn("no handler in tree", out)


class CommerceTests(unittest.TestCase):
    def test_bare_words_never_fire(self):
        t = Tree(self, {"q.sql": "SELECT * FROM t ORDER BY id;\n", "a.py": "class OrderedDict: pass\n",
                        "payment_terms.md": "# terms\n"})
        self.assertTrue(t.run().count("COMMERCE none"), "ORDER BY / OrderedDict / payment_terms.md must not fire")

    def test_schema_criterion(self):
        out = Tree(self, {"s.sql": "-- x\nCREATE TABLE orders (id int);\n"}).run()
        self.assertIn("2 orders/cart/products schema: s.sql:2", out)

    def test_payment_dependency_criterion(self):
        out = Tree(self, {"requirements.txt": "flask\nstripe==5\n"}).run()
        self.assertIn("1 payment dep: requirements.txt:2", out)
        self.assertIn("/ecommerce-cia", out)

    def test_dependency_name_is_a_whole_word(self):
        out = Tree(self, {"requirements.txt": "stripey==1\npayment_terms==1\n"}).run()
        self.assertIn("COMMERCE none", out)


class SecretsAndSkipsTests(unittest.TestCase):
    def test_env_is_named_never_read(self):
        out = Tree(self, {".env": "TOKEN=zz9secret\n", "a.py": "x = 1\n"}).run()
        self.assertIn(".env=present", out)
        self.assertNotIn("zz9secret", out)
        self.assertNotIn("zz9secret", Tree(self, {".env": "TOKEN=zz9secret\n"}).run("--json"))

    def test_secret_name_rules(self):
        for n in (".env", ".env.local", "k.pem", "k.key", "id_rsa", "id_rsa.pub"):
            self.assertTrue(route.is_secret(n), n)
        self.assertFalse(route.is_secret("id_helper.py"))

    def test_skipped_dirs_not_counted_but_named(self):
        files = {"a.py": "x = 1\n"}
        files.update({f"node_modules/p/f{i}.js": "x = 1\n" for i in range(300)})
        out = Tree(self, files).run()
        self.assertIn("1 source files", out)
        self.assertIn("skipped dirs: node_modules", out)


class GraphTests(unittest.TestCase):
    def test_mutual_imports_count_one_way_does_not(self):
        both = Tree(self, {"a/m.py": "import b\n", "b/m.py": "from a import m\n"}).run()
        self.assertIn("packages=2 cross-imports=1", both)
        one = Tree(self, {"a/m.py": "import b\n", "b/m.py": "x = 1\n"}).run()
        self.assertIn("packages=2 cross-imports=0", one)

    def test_js_relative_imports(self):
        out = Tree(self, {"a/x.js": "import y from '../b/y'\n", "b/y.js": "const a = require('../a/x')\n"}).run()
        self.assertIn("cross-imports=1", out)


class StateTests(unittest.TestCase):
    def test_enum_needs_a_status_word_nearby(self):
        out = Tree(self, {"a.py": 'status = (\n    "queued", "running",\n    "done")\n'}).run()
        self.assertIn("enums=1 (a.py:2 queued|running|done)", out)
        out = Tree(self, {"a.py": 'x = (\n    "queued", "running",\n    "done")\n'}).run()
        self.assertIn("enums=0", out)

    def test_renderer_coverage(self):
        out = Tree(self, {"a.py": 'status = ("a", "b", "c")\n', "r.py": 'R = {\n "a": 1,\n "b": 2,\n}\n'}).run()
        self.assertIn("renderers for 2 of 3 (r.py:2-3)", out)


class PinningTests(unittest.TestCase):
    def test_thresholds_match_the_doctrine(self):
        text = (ROOT / "references" / "code-graph-tools.md").read_text(encoding="utf-8")
        self.assertEqual(route.FILES_THRESHOLD, int(re.search(r"about (\d+) source files", text).group(1)))
        self.assertEqual(route.LINES_THRESHOLD, int(re.search(r"about ([\d,]+) lines", text).group(1).replace(",", "")))
        words = {"three": 3, "four": 4, "two": 2}
        self.assertEqual(route.PACKAGES_THRESHOLD,
                         words[re.search(r"(\w+) or more top-level packages", text).group(1)])

    def test_graph_signal_counts_match_the_doctrine(self):
        import route_render as rr
        text = (ROOT / "references" / "code-graph-tools.md").read_text(encoding="utf-8")
        sec1 = text.split("## 1.", 1)[1].split("## 2.", 1)[0]
        rows = [x for x in sec1.splitlines() if x.startswith("| ") and not x.startswith("| Signal")]
        self.assertEqual(rr.SIGNALS_TOTAL, len(rows))
        words = {"two": 2, "three": 3}
        self.assertEqual(rr.SIGNALS_NEEDED, words[re.search(r"when \*\*any (\w+)\*\*", sec1).group(1)])

    def test_graph_routing_matches_the_doctrine_table(self):
        """§2 says which graph is asked FIRST for each kind of question; the GRAPH line must say the same.
        Once printed "graphify, else cgc" for code questions, the reverse of §2, and nothing caught it."""
        import route_render as rr
        text = (ROOT / "references" / "code-graph-tools.md").read_text(encoding="utf-8")
        first = {row.split("|")[1]: row.split("|")[2] for row in text.splitlines() if row.startswith("| **")}
        code_first = next(v for k, v in first.items() if "Code relationships" in k)
        arch_first = next(v for k, v in first.items() if "Architectural context" in k)
        self.assertIn("CodeGraphContext", code_first)
        self.assertIn("graphify", arch_first)
        both = {"held": 2, "cgc": True, "graphify": True, "graphify_out": "fresh"}
        line = rr.graph_route(both)
        self.assertIn("code relationships → cgc", line)
        self.assertIn("architecture → graphify", line)
        self.assertIn("→ code graph ·", line)
        # cgc missing: code questions fall back to graphify, architecture unchanged
        self.assertIn("code relationships → graphify", rr.graph_route({**both, "cgc": False}))
        # stale or absent graphify-out/ is refreshed before it is asked
        self.assertIn("after `graphify update .`", rr.graph_route({**both, "graphify_out": "stale"}))
        # one or no scanned signal: the four judged signals decide, never a bare "code graph"
        self.assertIn("if one of the 4 judged signals holds, else grep", rr.graph_route({**both, "held": 1}))
        self.assertIn("grep unless 2 of the 4 judged signals hold", rr.graph_route({**both, "held": 0}))
        self.assertIn("grep (no graph tool on PATH)", rr.graph_route({**both, "cgc": False, "graphify": False}))

    def test_commerce_criteria_match_skill(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("payment-gateway code", "orders/cart/product schema",
                       "checkout/cart routes", "commerce framework dependency"):
            self.assertIn(phrase, text)
        out = Tree(self, {"a.py": "x = 1\n"}).run()
        for name in ("payment dep", "schema", "route", "framework"):
            self.assertIn(name, line_of(out, "COMMERCE"))


class CompanionTests(unittest.TestCase):
    def test_listed_other_and_missing(self):
        t = Tree(self, {"a.py": "x = 1\n"})
        (t.home / ".claude" / "skills" / "impeccable").mkdir(parents=True)
        (t.home / ".claude" / "skills" / "zzz").mkdir(parents=True)
        line = line_of(t.run(), "COMPANIONS")
        self.assertIn("installed: impeccable", line)
        self.assertIn("other skills 1", line)
        self.assertNotIn("zzz", line)
        missing = line.split("missing:")[1]
        self.assertIn("gemini", missing)
        self.assertNotIn("impeccable", missing)

    def test_only_skill_shaped_tokens_are_companions(self):
        """The kubai-icons row backticks what it delivers (`.svg`, `<img>`); the line once listed
        both as missing companions, which routes the run to install a file type."""
        import route_companions as rc
        names = rc.companion_names()
        self.assertIn("kubai-icons", names)
        self.assertIn("egm:egm-review", names)   # the leading slash of a command is dropped, the name kept
        for n in names:
            self.assertRegex(n, r"^[A-Za-z][\w-]*(:[\w-]+)?$")

    def test_plugin_namespaced_names(self):
        t = Tree(self, {"a.py": "x = 1\n"})
        out = line_of(t.run(), "COMPANIONS")
        self.assertIn("egm:egm-review", out.split("missing:")[1])
        (t.home / ".claude" / "plugins" / "marketplaces" / "egm").mkdir(parents=True)
        (t.home / ".claude" / "plugins" / "installed_plugins.json").write_text(
            '{"version": 2, "plugins": {"design@x": [{}]}}', encoding="utf-8")
        out = line_of(t.run(), "COMPANIONS")
        installed, missing = out.split("installed:")[1].split("missing:")
        self.assertIn("egm:egm-review", installed)
        self.assertIn("design:ux-copy", installed)
        self.assertNotIn("egm:", missing)
        self.assertNotIn("design:", missing)


class ContractTests(unittest.TestCase):
    def test_no_write_and_deterministic(self):
        t = Tree(self, {"a.py": 'X = "<table>"\n', "d/b.py": "import argparse\n", ".env": "T=1\n"})

        def digest():
            h = hashlib.sha256()
            for p in sorted(t.root.rglob("*")):
                h.update(str(p.relative_to(t.root)).encode())
                if p.is_file():
                    h.update(p.read_bytes())
            return h.hexdigest()

        before = digest()
        first, second = t.run(), t.run()
        self.assertEqual(before, digest())
        self.assertEqual(first, second)
        self.assertEqual(t.run("--json"), t.run("--json"))

    def test_output_is_short_and_none_always_has_the_boundary_line(self):
        for files in ({"a.py": "x = 1\n"}, {"README.md": "# hi\n"}, {}):
            out = Tree(self, files).run()
            self.assertLessEqual(len(out.splitlines()), 14)
            if "none" in out:
                self.assertIn("UNKNOWN not scanned", out)

    def test_unrecognised_stack_is_not_called_none(self):
        self.assertIn("stack not recognised", Tree(self, {"notes.txt": "hi\n"}).run())

    def test_missing_root_exits_2_and_never_1(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(route.main(["/no/such/dir/at/all"]), 2)


if __name__ == "__main__":
    unittest.main()
