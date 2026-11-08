#!/usr/bin/env python3
"""Structure guard for the cia skill - fails when its files stop agreeing with each other.

One job: keep the skill's own bookkeeping honest, so "nothing loose" is checked, not hoped for.
Stdlib only. Exit 0 = every check green; exit 1 = at least one check failed (CI runs this).

Checks:
  1. SKILL.md frontmatter: name present; description <= 1024 characters; no double quote inside it
     (the CI regex in .github/workflows/tests.yml cannot parse one).
  2. Nothing loose: every references/*.md, and every references/sweeps/*.md, is named by SKILL.md
     (a file path, or the sweeps/ folder). A file no index names is a file no reader is sent to.
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
}

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
    files = [SKILL, HERE / "README.md", *REFS.glob("*.md"), *SWEEPS.glob("*.md")]
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
