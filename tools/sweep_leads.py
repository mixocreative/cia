#!/usr/bin/env python3
"""Sweep leads: the S13 and S21 sites a script can list, so a run checks each one instead of hoping to notice it.

    python tools/sweep_leads.py <project-root>

Why it exists: across seven Codex audits of the fixture, six of the eight missed rows were never
cited anywhere in the report: the run read the file and did not notice the line (tests/RUNS.md,
"Other runtimes"). Rewording the sweeps did not change that (the site-list rule, reverted). Two
of the sweeps have sites a script finds every time, so a script lists them:

  * S13: a function or class defined in source whose name appears nowhere else in the tree:
    no call, no import, no config string. That is a capability with no caller, or one wired by a
    name this scan cannot see.
  * S21: a test that writes process-wide state (environment, working directory, import path)
    with no restore in sight: no cleanup, no patch, no `finally`, no tearDown. Every later test in
    the same process inherits it.

Leads, never verdicts. A lead is checked like any route.py line: a decorator-registered handler, a
plugin entry point or a framework hook is called from outside the tree and is not an orphan; a
restore in a shared fixture this scan does not follow is still a restore. The trap when
extending it: do not add a pattern that only the fixture has. Each one must name a class of
defect any project can hold, and the tests prove it on a project that is not the fixture.
Read-only, stdlib, the same tree walk and secret rules as route.py.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from route import walk, TEST_DIRS  # noqa: E402  one tree reader, one set of skip and secret rules

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DOC_EXTS = frozenset({".md", ".txt", ".rst"})
JS_EXTS = (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx")
JS_DEF = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)|"
                    r"^\s*(?:export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")
# Writes to state the whole test process shares. Each is a generic class, not a fixture's line.
GLOBAL_WRITE = re.compile(
    r"os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.(?:update|setdefault)\(|os\.putenv\(|"
    r"os\.chdir\(|sys\.path\.(?:insert|append)\(|process\.env\.\w+\s*=(?!=)|"
    r"process\.env\[[^\]]+\]\s*=(?!=)|process\.chdir\(")
RESTORE = re.compile(r"addCleanup|patch\.dict|monkeypatch|finally\s*:|tearDown|afterEach|afterAll|"
                     r"mock\.patch|restore|setUp\w*.*environ\.copy", re.I)


def is_test(rel: str) -> bool:
    parts = rel.split("/")
    name = parts[-1]
    return (any(p in TEST_DIRS for p in parts[:-1]) or name.startswith("test_")
            or re.search(r"[._-](test|spec)\.\w+$", name) is not None or name.endswith("_test.py"))


def definitions(rel: str, lines: list[str]) -> list[tuple[int, str]]:
    """(line, name) of every function and class a module defines, nested ones included."""
    if rel.endswith(".py"):
        try:
            tree = ast.parse("\n".join(lines))
        except SyntaxError:
            return []
        return [(n.lineno, n.name) for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if rel.endswith(JS_EXTS):
        out = []
        for i, line in enumerate(lines, 1):
            m = JS_DEF.match(line)
            if m:
                out.append((i, m.group(1) or m.group(2)))
        return out
    return []


def orphans(recs) -> list[tuple[str, int, str]]:
    """S13: source definitions whose name occurs exactly once in every readable file of the tree."""
    readable = [r for r in recs if r.lines is not None]
    counts: dict[str, int] = {}
    # Prose is not a caller: a design doc that names a function is exactly the "designed,
    # documented, unbuilt" S13 case, so docs must not count as the second occurrence. Config
    # files (yaml, json, toml) do count: dispatch by name lives there.
    for r in (r for r in readable if r.ext not in DOC_EXTS):
        for tok in re.findall(r"[A-Za-z_$][\w$]*", "\n".join(r.lines)):
            counts[tok] = counts.get(tok, 0) + 1
    out = []
    for r in readable:
        if is_test(r.rel):
            continue
        for ln, name in definitions(r.rel, r.lines):
            # Dunder methods and `main` are called by the runtime, never by name in the tree.
            if name.startswith("__") or name in ("main", "setUp", "tearDown") or len(name) < 3:
                continue
            if counts.get(name, 0) <= 1:
                out.append((r.rel, ln, name))
    return out


def unrestored(recs) -> list[tuple[str, int, str]]:
    """S21: a test line that writes process-wide state where the enclosing test shows no restore."""
    out = []
    for r in recs:
        if r.lines is None or not is_test(r.rel):
            continue
        file_restores = any(re.search(r"tearDown|afterEach|afterAll", l) for l in r.lines)
        for i, line in enumerate(r.lines, 1):
            m = GLOBAL_WRITE.search(line)
            if not m or file_restores:
                continue
            start = i - 1
            while start > 0 and not re.match(r"\s*(def |async def |it\(|test\(|function )", r.lines[start]):
                start -= 1
            end = i
            while end < len(r.lines) and not re.match(r"\s*(def |async def |it\(|test\(|class )", r.lines[end]):
                end += 1
            if not any(RESTORE.search(l) for l in r.lines[start:end]):
                out.append((r.rel, i, m.group(0).rstrip("=( ").strip()))
    return out


def report(root: str) -> str:
    recs, _, _, _ = walk(root)
    s13, s21 = orphans(recs), unrestored(recs)
    lines = ["LEADS (tools/sweep_leads.py, X0) - leads, never verdicts; each gets a finding or a reason on its sweep line"]
    lines += [f"S13 no caller in tree: {p}:{n} `{name}`" for p, n, name in s13] or ["S13 no caller in tree: none"]
    lines += [f"S21 process-wide state written in a test, no restore seen: {p}:{n} `{w}`" for p, n, w in s21] \
        or ["S21 process-wide state written in a test, no restore seen: none"]
    lines.append("boundary: Python by syntax tree, JS/TS by pattern; callers outside the tree, decorator or "
                 "entry-point registration, and restores in shared fixtures are not seen (evidence.md §E5)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or not Path(argv[0]).is_dir():
        print("usage: python tools/sweep_leads.py <project-root>", file=sys.stderr)
        return 2
    print(report(argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
