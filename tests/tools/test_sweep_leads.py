"""Guard tests for tools/sweep_leads.py, on a small project that is not the fixture."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import sweep_leads as sl  # noqa: E402

PROJECT = {
    "app/export.py": "def render_pdf(doc):\n    return doc\n\n\ndef export(doc):\n    return render_pdf(doc)\n",
    "app/sync.py": "def resync_all():\n    pass\n",                     # documented, never called
    "app/hooks.py": "def on_save(doc):\n    pass\n",                     # called by name from config
    "app/main.py": "from app.export import export\n\n\ndef main():\n    export({})\n",
    "config.yaml": "handlers:\n  save: on_save\n",
    "docs/DESIGN.md": "Every edit calls `resync_all` so the index stays fresh.\n",
    "web/util.js": "export function slugify(s) { return s }\nfunction unusedHelper() {}\nslugify('a')\n",
    "lib/notes.js": ("function used(x) { return x }\nfunction neverCalled() {}\n"
                     "used(1)\nmodule.exports = { used, neverCalled };\n"),
    "tests/test_export.py": (
        "import os\nimport unittest\n\n\nclass T(unittest.TestCase):\n"
        "    def test_leaks(self):\n        os.environ['MODE'] = 'x'\n        self.assertTrue(True)\n\n"
        "    def test_cleans(self):\n        self.addCleanup(os.environ.pop, 'B', None)\n"
        "        os.environ['B'] = 'y'\n"),
    "tests/test_cwd.py": "import os\n\n\ndef test_moves():\n    os.chdir('/tmp')\n",
}


class SweepLeadsTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        for rel, text in PROJECT.items():
            p = Path(d.name) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        self.out = sl.report(d.name)

    def test_orphans_include_a_documented_but_uncalled_function(self):
        self.assertIn("app/sync.py:1 `resync_all`", self.out)      # a doc mention is not a caller
        self.assertIn("web/util.js:2 `unusedHelper`", self.out)
        self.assertIn("lib/notes.js:2 `neverCalled`", self.out)        # an export line is not a caller

    def test_called_or_config_named_functions_are_not_orphans(self):
        for name in ("render_pdf", "export`", "on_save", "slugify", "`main`"):
            self.assertNotIn(name, self.out.split("S21")[0].split("\n", 1)[1])

    def test_unrestored_global_writes_in_tests(self):
        self.assertIn("tests/test_export.py:7", self.out)
        self.assertNotIn("tests/test_export.py:12", self.out)          # restored by addCleanup
        self.assertIn("tests/test_cwd.py:5", self.out)

    def test_leads_are_labelled_and_bounded(self):
        self.assertTrue(self.out.startswith("LEADS"))
        self.assertIn("never verdicts", self.out)
        self.assertIn("boundary:", self.out)


if __name__ == "__main__":
    unittest.main()
