#!/usr/bin/env python3
"""Build-mode report form and its checker: prints the build-standard §3a form, and names every block a report left out.

    python tools/build_report.py form              # the §3a form, read from build-standard.md
    python tools/build_report.py check <file|->    # exit 1 and a list when a block is missing

Why this is a tool and not more wording: four build runs in a row wrote correct, tested code and
then a prose summary in place of the §3a form. Four rewordings of "the report is the form" were
measured and reverted (tests/RUNS.md, build runs 4-8); two of those runs never opened
build-standard.md at all, so no sentence there could reach them. A command that prints the form,
and a check that names the missing block, reach a run that reads only SKILL.md §0.10a.

What it checks is shape, never truth. A block with the right words and wrong content passes here
and fails the scorer; that is the intended split. The trap to avoid when extending it: do not add
a check that only one fixture can satisfy (a function name, a file path). Each pattern below must
hold for any primary-path write in any project.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp950/cp1252
    sys.stdout.reconfigure(encoding="utf-8")

STANDARD = Path(__file__).resolve().parents[1] / "references" / "build-standard.md"

# layer.family.name@version, three dotted parts at least (evidence.md §E3).
OBL_ID = re.compile(r"\b([A-Za-z][\w-]*(?:\.[\w-]+){2,}@\d+)\b")
CASE_KINDS = ("concurrent", "fault-after-first-write", "duplicate", "refused")
PROPERTIES = ("atomic", "race-free", "idempotent", "loud")
LINE_14 = ("SURFACE", "JOURNEY", "DESIGN", "GRAPH", "EXECUTORS", "TESTS", "COMPANIONS")


def form_text(standard_md: str) -> str:
    """The first fenced block after the §3a heading: one copy of the form, in build-standard.md."""
    part = standard_md.split("## §3a", 1)
    if len(part) < 2:
        raise ValueError("build-standard.md has no §3a heading")
    m = re.search(r"```text\n(.*?)```", part[1], re.S)
    if not m:
        raise ValueError("build-standard.md §3a has no ```text block")
    return m.group(1)


def identifier(obl_id: str) -> str:
    """queue.claim.exactly-once@1 -> queue_claim_exactly_once_1, the form a test name can carry."""
    return re.sub(r"\W+", "_", obl_id).strip("_").lower()


def checks(report: str) -> list[tuple[str, bool, str]]:
    """(block, present, what to add) for every §3a block, in form order."""
    low = report.lower()
    ids = OBL_ID.findall(report)
    obl = ids[0] if ids else ""
    tests = {t.lower() for t in re.findall(r"\btest_\w+", report)}
    carrying = {t for t in tests if obl and identifier(obl) in t}
    out = [
        ("mode", bool(re.search(r"(?im)^\W*mode:\s*build mode", report)),
         "first line 'Mode: build mode - <operation>, <file>'"),
        ("obligation id", bool(obl), "an ID in layer.family.name@version form, before any code"),
        ("obligation fields", bool(re.search(r"\bA[2-5]\b", report))
         and all(k in low for k in CASE_KINDS) and '"' in report,
         "authority A2 or higher, the case kinds " + ", ".join(CASE_KINDS)
         + ", and the owner's words in quotes"),
        ("primary quantity", "primary quantity" in low and "observ" in low,
         "'Primary quantity and observers:' line"),
        ("proofs named", all(p in low for p in PROPERTIES),
         "the four proofs named " + " / ".join(PROPERTIES)),
        ("red output pasted", bool(re.search(r"(?m)^\s*(FAIL|ERROR)\b|AssertionError|Traceback|FAILED", report)),
         "the runner's failing output, pasted, from before the implementation"),
        ("green output pasted", bool(re.search(r"Ran \d+ tests?", report))
         and bool(re.search(r"(?m)^\s*OK\b", report)),
         "the runner's passing output ('Ran N tests ... OK'), pasted"),
        ("test names carry the id", len(carrying) >= 4,
         f"four test names containing '{identifier(obl) or '<obligation id>'}'"),
        ("ledger row", bool(re.search(r"\|\s*(PASS|PARTIAL|FAIL)\s*\|", report))
         and bool(re.search(r"A\d\s*/\s*A\d", report)),
         "ledger row: | capability | PASS/PARTIAL/FAIL | A<required> / A<reached> | artefact | covered |"),
        ("closure gates", all(re.search(rf"\bCG{n}\b", report) for n in range(1, 14)),
         "CG1 ... CG13, each a count or n/a with a reason (missing: "
         + ", ".join(f"CG{n}" for n in range(1, 14) if not re.search(rf"\bCG{n}\b", report)) + ")"),
        ("line 14", all(re.search(rf"\b{k}\b", report) for k in LINE_14),
         "Step 6 line 14 with " + " · ".join(LINE_14) + ", each filled or n/a with a reason"),
        ("debt not taken", "debt" in low, "'Debt not taken' with the reason, or 'none'"),
        ("receipts", "receipt" in low, "the receipts line, one quoted phrase per reference read"),
    ]
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["form"]:
        print(form_text(STANDARD.read_text(encoding="utf-8")), end="")
        return 0
    if argv[:1] != ["check"] or len(argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    src = argv[1]
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    results = checks(text)
    for name, ok, hint in results:
        print(f"{'ok     ' if ok else 'MISSING'}  {name}" + ("" if ok else f" - add {hint}"))
    missing = sum(not ok for _, ok, _ in results)
    print(f"build_report: {len(results) - missing} of {len(results)} blocks present"
          + ("" if not missing else " - fill the missing blocks, check again, then reply with the report"))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
