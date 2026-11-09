"""Guard tests for tools/inventory.py, on a made-up project that is not a fixture."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import inventory  # noqa: E402

PROJECT = {
    "settings.yaml": "port: 8080\ntheme: dark\n",
    "app/store.py": ('"""Insert a note into the store."""\n\n\ndef save(conn, note):\n'
                     '    conn.execute("INSERT INTO notes VALUES (?)", (note,))\n\n\n'
                     'def export(path, text):\n    path.write_text(text)\n'),
    "web/sync.js": "function push(f, s) {\n  fs.writeFile(f, s);\n}\nmodule.exports = { push };\n",
    "tests/test_store.py": "def test_save():\n    assert True\n",
    "web/sync.test.js": "test('push writes the file', () => {});\n",
}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        for rel, text in PROJECT.items():
            p = Path(d.name) / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        self.root = d.name
        self.out = inventory.report(d.name)

    def test_every_kind_is_listed_with_its_line(self):
        for line in ("key    settings.yaml:1  `port`", "def    app/store.py:4  `save`",
                     "write  app/store.py:5  `INSERT INTO notes`", "write  app/store.py:9  `.write_text(`",
                     "def    web/sync.js:1  `push`", "write  web/sync.js:2", "test   tests/test_store.py:1  `test_save`",
                     "test   web/sync.test.js:1  `push writes the file`"):
            self.assertIn(line, self.out)

    def test_a_docstring_word_is_not_a_write(self):
        self.assertNotIn("app/store.py:1", self.out)

    def test_the_cap_says_what_it_left(self):
        out = inventory.report(self.root, cap=3)
        self.assertEqual(len([x for x in out.splitlines() if x[:5].strip() in ("def", "test", "key", "write")]), 3)
        self.assertIn("more not listed", out)
        self.assertIn("UNVERIFIED", out)


if __name__ == "__main__":
    unittest.main()
