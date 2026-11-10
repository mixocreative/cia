"""Guard test: every runnable tool answers --help with what it is for, and exits 0 without doing its job.

Why: twelve tools parsed argv by hand, and `--help` either ran the job (score.py printed the score,
sweep-diff.py ran the comparison) or came back as exit 2. A stranger's first command is --help.
"""
import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "tools"
# A file with no entry guard is a module (route_tree.py and its siblings), not a command.
RUNNABLE = sorted(p for p in TOOLS.glob("*.py") if '__name__ == "__main__"' in p.read_text(encoding="utf-8"))


class HelpTests(unittest.TestCase):
    def test_every_tool_is_found(self):
        self.assertGreaterEqual(len(RUNNABLE), 14)   # a glob that matches nothing would pass the loop below

    def test_help_exits_zero_and_says_what_the_tool_is(self):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        for tool in RUNNABLE:
            for flag in ("--help", "-h"):
                with self.subTest(tool=tool.name, flag=flag):
                    r = subprocess.run([sys.executable, str(tool), flag], capture_output=True,
                                       encoding="utf-8", env=env, timeout=30)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    first = ast.get_docstring(ast.parse(tool.read_text(encoding="utf-8"))).splitlines()[0]
                    # argparse tools print their own usage; the hand-parsed ones print the docstring
                    self.assertTrue(first in r.stdout or r.stdout.lower().startswith("usage:"), r.stdout[:200])


if __name__ == "__main__":
    unittest.main()
