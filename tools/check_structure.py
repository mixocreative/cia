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
  7. Version: plugin.json, marketplace.json and CITATION.cff carry one version, and CHANGELOG.md has an
     entry for it. Three hand-edited copies drift; a release with no entry is a release nobody can read.
  8. Tools map: every file in tools/ is named in tools/README.md, and the map names no file that is gone.
     A map that lags the folder sends the next reader to the wrong file.
  9. Line length: no line of SKILL.md or a reference over READ_LIMIT characters. The trap: the Read tool
     cuts a longer line, and on 2026-11-10 ecommerce-cia's Step 3 lost half its reading list that way.

Usage: python tools/check_structure.py
"""
import json
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
# tools/route.py (843 lines) was cut on 2026-11-09 by job: route_tree.py (the walk), route_companions.py,
# route_render.py; output byte-identical before and after.
DEBT: dict[str, str] = {}

# SKILL.md was at the 600 limit until 2026-11-09, when the two named duplicates were cut: §0.4 (it restated
# §0.2-§0.3) and Step 4's restatement of browser-walks.md §8a and §10 (now pointers). Next cut when it
# nears 600 again: none of the rest is a duplicate. Step 4 (a)-(g), the S22 guards and the Final Question
# live only in SKILL.md, so moving them is a doctrine change, run-tested.

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


def check_tools_map() -> None:
    tools = HERE / "tools"
    if not (tools / "README.md").is_file():
        fail("tools/README.md is missing: the folder map (one row per file, saying its job)")
        return
    files = {p.name for p in tools.iterdir() if p.is_file() and p.name != "README.md"}
    named = set(re.findall(r"^\| `([^`]+)` \|", read(tools / "README.md"), re.M))
    for name in sorted(files - named):
        fail(f"tools/README.md does not name tools/{name}: add a row saying its job")
    for name in sorted(named - files):
        fail(f"tools/README.md names tools/{name}, which does not exist: remove the row")


def check_version() -> None:
    plugin = json.loads(read(HERE / ".claude-plugin" / "plugin.json"))["version"]
    market = json.loads(read(HERE / ".claude-plugin" / "marketplace.json"))["plugins"][0]["version"]
    # ^version, not cff-version: that line is the citation format's own version (1.2.0), and a bump by
    # search-and-replace once rewrote it to the skill's.
    cff = re.search(r"^version: (\S+)", read(HERE / "CITATION.cff"), re.M)
    found = {"plugin.json": plugin, "marketplace.json": market, "CITATION.cff": cff.group(1) if cff else "none"}
    if len(set(found.values())) != 1:
        fail("version: " + ", ".join(f"{k} says {v}" for k, v in found.items()))
    if f"## [{plugin}]" not in read(HERE / "CHANGELOG.md"):
        fail(f"CHANGELOG.md has no entry for {plugin}, the version in plugin.json")


READ_LIMIT = 2000   # characters per line the Read tool shows; past it, a run never sees the rest


def check_line_length() -> None:
    for f in [SKILL, *REFS.glob("*.md"), *SWEEPS.glob("*.md")]:
        for i, line in enumerate(read(f).splitlines(), 1):
            if len(line) > READ_LIMIT:
                fail(f"{rel(f)}:{i} is {len(line)} characters; the Read tool cuts it at {READ_LIMIT}: wrap it")


def main() -> int:
    skill_text = read(SKILL)
    check_frontmatter(skill_text)
    check_nothing_loose_or_missing(skill_text)
    check_agents_and_keys(skill_text)
    check_sweeps()
    check_stale_paths()
    check_size()
    check_line_length()
    check_version()
    check_tools_map()
    if failures:
        print(f"check_structure: {len(failures)} failure(s)")
        for msg in failures:
            print(f"  - {msg}")
        return 1
    print("check_structure: all green")
    return 0


if __name__ == "__main__":
    if {"-h", "--help"} & set(sys.argv[1:]):   # answered here, before main(): --help must never run the job
        sys.stdout.reconfigure(encoding="utf-8")
        print(__doc__)
        sys.exit(0)
    sys.exit(main())
