#!/usr/bin/env python3
"""Structure guard for the cia skill - fails when its files stop agreeing with each other.

One job: keep the skill's own bookkeeping honest, so "nothing loose" is checked, not hoped for.
Stdlib only. Exit 0 = every check green; exit 1 = at least one check failed (CI runs this).

Checks:
  1. SKILL.md frontmatter: name present; description <= 1024 characters; no double quote inside it
     (the CI regex in .github/workflows/tests.yml cannot parse one).
  2. Nothing loose: every references/*.md, and every references/sweeps/*.md, is named by SKILL.md
     (a file path, or the sweeps/ folder). A file no index names is a file no reader is sent to.
     Also: every agents/*.md is named by SKILL.md or references/agent-deployment.md, and every
     tests/EXPECTED-*.md is named in tests/RUNBOOK.md (an answer key no run book points to is never scored).
  3. Nothing missing: every references/... path SKILL.md names exists.
  4. Sweeps S1-S24: each sweep heading appears exactly once across references/sweeps/*.md.
  5. No stale path: no `references/sweeps.md` left in a live doc (historical wording is allowed).
  6. Size: no file over HARD_LIMIT lines (the cut is taken); a file over DEBT_LIMIT lines needs an
     entry in DEBT with its next cut written down (code principle 5). An entry for a file that is
     now under the limit fails too, so a paid-off debt is removed rather than left to rot.

Usage: python tools/check_structure.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REFS = HERE / "references"
SWEEPS = REFS / "sweeps"
SKILL = HERE / "SKILL.md"

HARD_LIMIT = 1000   # over this, the cut is taken in the same change
DEBT_LIMIT = 600    # over this, the file is named as debt below, with its next cut

# file (relative to HERE) -> the next cut, written down. Empty when nothing is over DEBT_LIMIT.
DEBT = {
    "tools/route.py": "move the pattern and constant tables (SURFACE regexes, STATE_WORD/QLIST/CLIST, "
                      "PY_IMPORT/JS_REL, the *_DEPS word lists, SCHEMA_RES) to tools/route_patterns.py: "
                      "pure data, importable and testable without a scan",
}

# Named, not yet debt: SKILL.md sits at the limit. A file AT the limit cannot carry a DEBT entry
# (the stale-entry check below refuses it), so its next cut lives here. When an edit would cross
# 600, cut the two real duplicates first, one gate pair for the move: Step 4's browser-walk
# restatement (it repeats browser-walks.md §12-§13; keep a six-line pointer) and §0.4 (it restates
# §0.2-§0.3; keep six lines). Step 4 (a)-(g), the S22 guards and the Final Question are NOT
# duplicates: they live only in SKILL.md, so moving them is a doctrine change, run-tested.

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def rel(p: Path) -> str:
    return p.relative_to(HERE).as_posix()


def check_frontmatter(skill_text: str) -> None:
    m = re.match(r'---\nname: (\S+)\ndescription: "(.*)"\n---\n', skill_text.replace("\r\n", "\n"), re.S)
    if not m:
        fail("SKILL.md: frontmatter does not match the CI pattern (name, then description in double quotes)")
        return
    desc = m.group(2)
    if len(desc) > 1024:
        fail(f"SKILL.md: description is {len(desc)} characters; the limit is 1024")
    if '"' in desc:
        fail("SKILL.md: description contains a double quote, which the CI regex cannot parse")


def check_nothing_loose_or_missing(skill_text: str) -> None:
    named = {m.rstrip(".") for m in re.findall(r"references/[A-Za-z0-9_./-]+", skill_text)}
    # A tool SKILL tells the AI to run (tools/route.py at step 0) must exist, or step 0 fails on every run.
    for tool in sorted(set(re.findall(r"tools/[A-Za-z0-9_-]+\.py", skill_text))):
        if not (HERE / tool).exists():
            fail(f"SKILL.md names {tool} but that file does not exist")
    sweeps_folder_named = "references/sweeps/" in skill_text
    for name in sorted(named):
        target = HERE / name
        if name.endswith("/"):
            if not target.is_dir():
                fail(f"SKILL.md names {name} but that folder does not exist")
        elif not target.exists():
            fail(f"SKILL.md names {name} but that file does not exist")
    for f in sorted(REFS.glob("*.md")):
        if rel(f) not in named:
            fail(f"loose file: {rel(f)} is not named by SKILL.md")
    for f in sorted(SWEEPS.glob("*.md")):
        if not sweeps_folder_named and rel(f) not in named:
            fail(f"loose file: {rel(f)} is not reachable from SKILL.md (sweeps/ folder not named)")


def check_agents_and_keys(skill_text: str) -> None:
    # Agent briefs and answer keys sit outside references/, so check 2 cannot see them; without this
    # a brief nobody routes to, or a key nobody scores against, would sit there looking finished.
    routed = skill_text + read(REFS / "agent-deployment.md")
    for f in sorted((HERE / "agents").glob("*.md")):
        if rel(f) not in routed:
            fail(f"loose file: {rel(f)} is not named by SKILL.md or references/agent-deployment.md")
    runbook = read(HERE / "tests" / "RUNBOOK.md")
    for f in sorted((HERE / "tests").glob("EXPECTED-*.md")):
        if f.name not in runbook:
            fail(f"loose file: {rel(f)} is not named in tests/RUNBOOK.md")


def check_sweeps() -> None:
    found: dict[str, int] = {}
    for f in sorted(SWEEPS.glob("*.md")):
        for s in re.findall(r"^## (S\d+) ", read(f), flags=re.M):
            found[s] = found.get(s, 0) + 1
    for n in range(1, 25):
        key = f"S{n}"
        if found.get(key, 0) != 1:
            fail(f"sweep {key}: found {found.get(key, 0)} headings across references/sweeps/ (expected exactly 1)")


def check_stale_paths() -> None:
    stale = re.compile(r"(?<!former `)references/sweeps\.md")
    live = [HERE / "SKILL.md", HERE / "README.md", *REFS.glob("*.md"), *SWEEPS.glob("*.md"),
            *(HERE / "tests").glob("*.md")]
    for f in live:
        if f.name == "RUNS.md":  # the run log quotes history on purpose
            continue
        for i, line in enumerate(read(f).splitlines(), 1):
            if stale.search(line):
                fail(f"stale path {rel(f)}:{i} names references/sweeps.md, which was split into references/sweeps/")


def check_size() -> None:
    # Code counts too: a size rule that reads only the docs let an 843-line tool grow unnamed.
    files = [SKILL, HERE / "README.md", *REFS.glob("*.md"), *SWEEPS.glob("*.md"),
             *(HERE / "tools").glob("*.py"), *(HERE / "tests" / "harness").glob("*.py"),
             *(HERE / "tests" / "tools").glob("*.py")]
    over_debt = set()
    for f in files:
        n = len(read(f).splitlines())
        key = rel(f)
        if n > HARD_LIMIT:
            fail(f"{key} is {n} lines; over {HARD_LIMIT} the cut is taken, not named")
        if n > DEBT_LIMIT:
            over_debt.add(key)
            if key not in DEBT:
                fail(f"{key} is {n} lines; over {DEBT_LIMIT} it must be named in DEBT with its next cut")
    for key in DEBT:
        if key not in over_debt:
            fail(f"DEBT entry {key} is no longer over {DEBT_LIMIT} lines: remove the entry")


def main() -> int:
    skill_text = read(SKILL)
    check_frontmatter(skill_text)
    check_nothing_loose_or_missing(skill_text)
    check_agents_and_keys(skill_text)
    check_sweeps()
    check_stale_paths()
    check_size()
    if failures:
        print(f"check_structure: {len(failures)} failure(s)")
        for msg in failures:
            print(f"  - {msg}")
        return 1
    print("check_structure: all green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
