"""Guards for agents/*.md: thin definitions, one source of truth in references/."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS = sorted((ROOT / "agents").glob("*.md"))
REFS = list((ROOT / "references").glob("*.md")) + list((ROOT / "references" / "sweeps").glob("*.md"))
MIN_DUP = 60  # a line this long copied from a reference is doctrine duplicated


def split(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, text)


def duplicated_lines(agent_text, ref_texts):
    """Lines of >= MIN_DUP chars in agent_text found verbatim in any reference text."""
    out = []
    for line in agent_text.splitlines():
        s = line.strip()
        if len(s) >= MIN_DUP and any(s in r for r in ref_texts):
            out.append(s)
    return out


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.refs = [p.read_text(encoding="utf-8") for p in REFS]

    def test_three_agents_exist(self):
        names = {p.name for p in AGENTS}
        for n in ("cia-cold-auditor.md", "cia-surface-mapper.md", "cia-site-reviewer.md"):
            self.assertIn(n, names)

    def test_frontmatter_and_body_size(self):
        for p in AGENTS:
            fm, body = split(p.read_text(encoding="utf-8"))
            self.assertIsNotNone(fm, p.name)
            for key in ("name", "description", "tools", "model"):
                self.assertRegex(fm, rf"(?m)^{key}:\s*\S", f"{p.name} lacks {key}")
            self.assertLessEqual(len(body.strip().splitlines()), 25, p.name)

    def test_cited_sections_exist(self):
        for p in AGENTS:
            text = p.read_text(encoding="utf-8")
            for f, n in re.findall(r"references/([\w./-]+\.md) §(\d+)", text):
                ref = ROOT / "references" / f
                self.assertTrue(ref.exists(), f"{p.name}: {f} missing")
                body = ref.read_text(encoding="utf-8")
                ok = re.search(rf"(?m)^#+\s*{n}[.\s]", body) or f"§{n}" in body
                self.assertTrue(ok, f"{p.name}: {f} has no section {n}")

    def test_no_duplicated_reference_lines(self):
        for p in AGENTS:
            self.assertEqual(duplicated_lines(p.read_text(encoding="utf-8"), self.refs), [], p.name)

    def test_duplication_guard_can_fail(self):
        long = next(ln.strip() for r in self.refs for ln in r.splitlines() if len(ln.strip()) >= MIN_DUP)
        fake = "---\nname: x\n---\nok line\n" + long + "\n"
        self.assertEqual(duplicated_lines(fake, self.refs), [long])

    def test_no_sweep_headings(self):
        for p in AGENTS:
            self.assertIsNone(re.search(r"(?m)^##\s*S\d", p.read_text(encoding="utf-8")), p.name)

    def test_plugin_json_lists_every_agent_file(self):
        # Claude Code's manifest schema wants each agents entry to be a .md file: "./agents" (a folder) made the
        # whole plugin fail to load ("agents.0: must end with .md"), found by an end-to-end --plugin-dir run.
        data = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertTrue(all(a.endswith(".md") for a in data["agents"]), data["agents"])
        self.assertEqual(sorted(data["agents"]), [f"./agents/{p.name}" for p in AGENTS])


if __name__ == "__main__":
    unittest.main()
