#!/usr/bin/env python3
"""Inventory: every function, test, config key and file write in the project, so a run can give each one a disposition.

    python tools/inventory.py <project-root> [--max N]

Why it exists: Codex audits of fixture-service missed one or two planted rows per run, a different
one each time (tests/RUNS.md, "Other runtimes"), and most misses were never cited at all: the run
read the file and did not notice the line. A rule that each sweep list its sites did not help (the
run chose the sites), and a scan of two defect classes only moved the misses to other rows. This
list is exhaustive by construction: a script enumerates the items, and the run's job is to say
one word about each, which is how a line that was read but not noticed gets noticed.

It lists, never grades. Four kinds, each a place the sweeps look:
  * def    a function or class in source (S13 callers, S2/S3 bodies, S12 failure paths)
  * test   a test function (S21: what it proves, what it leaves behind)
  * key    a top-level configuration key (S5: who reads it)
  * write  a line that writes a file, a table row or process state (S1/S2/S12/S20: who reads it back)

On a large project pass the primary path's directory as the root, not the whole tree.
Bounded on purpose: past --max items (default 150) it lists the first N in path order and says how
many it left, because a list nobody can finish is a list nobody reads. Read-only, stdlib, the same
tree walk and secret rules as route.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_tree import walk  # noqa: E402  one tree reader, one set of skip and secret rules
from sweep_leads import definitions, is_test  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEST_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(test\w*)\(|^\s*(?:test|it)\(\s*['\"]([^'\"]{1,80})")
# Generic writes: files, rows, process state. Each pattern is a class any project has, not a fixture's line.
WRITE = re.compile(
    r"\.write_text\(|\.write_bytes\(|open\([^)]*['\"][wa]b?\+?['\"]|\bfs\.(?:promises\.)?(?:writeFile|appendFile|rename)\w*\(|"
    r"\bwriteFile(?:Sync)?\(|\brename(?:Sync)?\(|\b(?:INSERT|UPDATE|DELETE)\s+(?:INTO\s+|FROM\s+)?\w+|"
    r"os\.environ\[[^\]]+\]\s*=(?!=)|process\.env\.\w+\s*=(?!=)")  # case-sensitive: "Insert a" in a docstring is not SQL
YAML_KEY = re.compile(r"^([A-Za-z_][\w-]*)\s*:")
CONFIG_NAMES = re.compile(r"(?:^|/)(?:config|settings|app)[\w.-]*\.(?:ya?ml|json|toml)$|\.env\.example$", re.I)


def config_keys(rel: str, lines: list[str]) -> list[tuple[int, str]]:
    if rel.endswith(".json"):
        try:
            data = json.loads("\n".join(lines))
        except ValueError:
            return []
        out = []
        for key in data if isinstance(data, dict) else []:
            ln = next((i for i, x in enumerate(lines, 1) if f'"{key}"' in x), 1)
            out.append((ln, key))
        return out
    return [(i, m.group(1)) for i, x in enumerate(lines, 1) if (m := YAML_KEY.match(x))]


def items(recs) -> list[tuple[str, int, str, str]]:
    """(path, line, kind, name) for every inventoried item, in path then line order."""
    out = []
    for r in recs:
        if r.lines is None:
            continue
        if is_test(r.rel):
            for i, x in enumerate(r.lines, 1):
                m = TEST_DEF.match(x)
                if m:
                    out.append((r.rel, i, "test", m.group(1) or m.group(2)))
        else:
            out += [(r.rel, ln, "def", name) for ln, name in definitions(r.rel, r.lines)]
        if CONFIG_NAMES.search(r.rel):
            out += [(r.rel, ln, "key", k) for ln, k in config_keys(r.rel, r.lines)]
        if r.rel.endswith((".py", ".js", ".mjs", ".cjs", ".ts", ".go", ".rb", ".php")):
            for i, x in enumerate(r.lines, 1):
                m = WRITE.search(x)
                if m:
                    out.append((r.rel, i, "write", " ".join(m.group(0).split())[:40]))
    return sorted(out)


def report(root: str, cap: int = 150) -> str:
    recs, _, _, _ = walk(root)
    found = items(recs)
    shown = found[:cap]
    lines = [f"INVENTORY (tools/inventory.py, X0) - {len(found)} items; give each ONE disposition in the "
             f"report's inventory table: a finding id, a control, or 'read, nothing'"]
    lines += [f"{kind:5}  {path}:{ln}  `{name}`" for path, ln, kind, name in shown]
    if len(found) > cap:
        lines.append(f"... {len(found) - cap} more not listed (--max {cap}); name the modules they sit in as "
                     f"UNVERIFIED rather than dispositioning a sample")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cap = 150
    if "--max" in argv:
        i = argv.index("--max")
        cap, argv = int(argv[i + 1]), argv[:i] + argv[i + 2:]
    if len(argv) != 1 or not Path(argv[0]).is_dir():
        print("usage: python tools/inventory.py <project-root> [--max N]", file=sys.stderr)
        return 2
    print(report(argv[0], cap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
