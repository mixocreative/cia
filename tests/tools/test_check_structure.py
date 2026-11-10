"""Guard test for check 8 of tools/check_structure.py (the tools/ map), on a made-up folder.

Checks 1-7 are exercised only by CI running the tool on the real repo, which proves they pass and
never that they can fail: debt, named here so it is not mistaken for coverage.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import check_structure as cs  # noqa: E402


class ToolsMapTests(unittest.TestCase):
    def run_check(self, files, readme):
        with tempfile.TemporaryDirectory() as d:
            tools = Path(d) / "tools"
            tools.mkdir()
            for name in files:
                (tools / name).write_text("", encoding="utf-8")
            if readme is not None:
                (tools / "README.md").write_text(readme, encoding="utf-8")
            with mock.patch.object(cs, "HERE", Path(d)), mock.patch.object(cs, "failures", []) as out:
                cs.check_tools_map()
                return list(out)

    def test_map_and_folder_agree(self):
        self.assertEqual(self.run_check(["a.py", "pre-push"], "| `a.py` | x |\n| `pre-push` | y |\n"), [])

    def test_a_file_the_map_does_not_name_fails(self):
        out = self.run_check(["a.py", "b.py"], "| `a.py` | x |\n")
        self.assertEqual(len(out), 1)
        self.assertIn("does not name tools/b.py", out[0])

    def test_a_row_for_a_file_that_is_gone_fails(self):
        out = self.run_check(["a.py"], "| `a.py` | x |\n| `gone.py` | y |\n")
        self.assertIn("names tools/gone.py, which does not exist", out[0])

    def test_no_map_fails(self):
        self.assertIn("tools/README.md is missing", self.run_check(["a.py"], None)[0])


if __name__ == "__main__":
    unittest.main()
