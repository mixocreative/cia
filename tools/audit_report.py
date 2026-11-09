#!/usr/bin/env python3
"""Audit report checker: names every part of a §0.6 report that is missing, including each reference the run did not read.

    python tools/audit_report.py check <file|->

Run it from the skill directory before the final reply, with the report on stdin (an audit has no
Write tool, so a here-document is the way in):  python tools/audit_report.py check - <<'EOF' ... EOF

Why this is a tool and not more wording: on byte-identical doctrine, some runs read the references
and some stop at SKILL.md, and the ones that stop lose a planted row (RUNS, "the reading collapse";
run ED on fixture-editor, 2026-11-09: receipts 0/19, one row missed). SKILL already says no finding
before the receipts; a sentence did not hold every run. A receipt is a phrase that appears once in
one reference, so this checks each quoted receipt against the reference it belongs to: a run that
did not reach a file cannot pass by guessing, and the MISSING line names the file to read. The same
mechanism fixed build mode's report form (tools/build_report.py).

Shape, never truth: the scorer still judges the findings. The trap when extending it: no check
may name a fixture's file, function or defect.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from receipts import scan  # noqa: E402  the receipt of each reference, read from the references

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Read on every Screen audit (SKILL Step 2 order); surface-map and journey-map join when the ROUTE
# block shows a page, a CLI or a route.
ALWAYS = ("theory.md", "sweeps/", "wiring-walk.md", "doctrine.md", "reporting.md", "evidence.md", "browser-walks.md")
WITH_SURFACE = ("surface-map.md", "journey-map.md")
SURFACE = re.compile(r"page=(\d+)\D+cli=(\d+)\D+(?:http )?routes=(\d+)")
LEAD = re.compile(r"^\s*S(?:13|21)\b[^:]*:\s*([\w./-]+:\d+)\s+`([^`]+)`", re.M)


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[_*`\"“”'’]", " ", text).lower().split())


def receipts_missing(report: str, need: tuple[str, ...]) -> list[str]:
    found, _ = scan()
    by_key = {("sweeps/" if k.startswith("sweeps/") else k): phrase for k, phrase in found.items()}
    body = _norm(report)
    return [ref for ref in need if ref in by_key and _norm(by_key[ref]) not in body]


def leads_left(report: str) -> list[str]:
    """Each lead the LEADS block lists must be named again outside the block: a finding or a reason."""
    block = report.split("LEADS (tools/sweep_leads.py", 1)
    if len(block) < 2:
        return []
    head, rest = block
    lines = rest.splitlines()
    end = next((i for i, x in enumerate(lines) if x.strip().startswith("boundary:")), min(len(lines), 40))
    leads, after = "\n".join(lines[:end]), head + "\n".join(lines[end + 1:])
    return [site for site, name in LEAD.findall(leads) if site not in after and name not in after]


ITEM = re.compile(r"^(def|test|key|write)\s+([\w./-]+:\d+)\s+`([^`]*)`", re.M)


def inventory_left(report: str) -> list[str]:
    """When the run pasted an INVENTORY block (Codex, SKILL §0.5), every item must be named again
    outside it: a finding, a control, or 'read, nothing'. An item named only in the block was listed,
    not read."""
    block = report.split("INVENTORY (tools/inventory.py", 1)
    if len(block) < 2:
        return []
    head, rest = block
    lines = rest.splitlines()
    end = next((i for i, x in enumerate(lines[1:], 1) if not ITEM.match(x) and not x.startswith("...")), len(lines))
    items, after = "\n".join(lines[:end]), head + "\n".join(lines[end:])
    return [site for kind, site, name in ITEM.findall(items) if site not in after]


def checks(report: str) -> list[tuple[str, bool, str]]:
    surface = SURFACE.search(report)
    # SKILL: SURFACE and JOURNEY may be n/a only when the block shows page=0, cli=0 and routes=0, so the
    # two maps are required unless the report shows exactly that.
    has_surface = not surface or any(int(n) for n in surface.groups())
    need = ALWAYS + (WITH_SURFACE if has_surface else ())
    missing_receipts = receipts_missing(report, need)
    leads = leads_left(report)
    sweeps = [n for n in range(1, 25) if not re.search(rf"\bS{n}\b", report)]
    numbered = {int(n) for n in re.findall(r"(?m)^\s*(?:\*\*)?(\d{1,2})[.)]", report)}
    lines14 = [n for n in range(1, 15) if n not in numbered]
    out = [
        # Present means run and named; a summary of the block counts. Pasting it verbatim is SKILL's rule,
        # but demanding the exact text here would fail sound reports for their formatting.
        ("ROUTE block", "route.py" in report or bool(surface),
         "the ROUTE block from `python tools/route.py <root>`"),
        ("LEADS block", "sweep_leads" in report or "LEADS" in report,
         "the LEADS block from `python tools/sweep_leads.py <root>`"),
        ("every lead answered", not leads,
         "a finding or a one-line reason on its sweep for " + ", ".join(leads)),
        ("receipts", not missing_receipts,
         "the receipt of " + ", ".join(missing_receipts) + " - read each file to its receipt line, then quote it"),
        ("sweep lines S1-S24", not sweeps, "a line for " + ", ".join(f"S{n}" for n in sweeps)),
        ("Step 6 lines 1-14", not lines14, "numbered line " + ", ".join(map(str, lines14))),
    ]
    inv = inventory_left(report)
    if "INVENTORY (tools/inventory.py" in report:
        out.append(("every inventory item answered", not inv,
                    f"a disposition (finding id, control, or 'read, nothing') for {len(inv)} item(s): "
                    + ", ".join(inv[:12]) + (" ..." if len(inv) > 12 else "")))
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] != ["check"] or len(argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    text = sys.stdin.read() if argv[1] == "-" else Path(argv[1]).read_text(encoding="utf-8")
    results = checks(text)
    for name, ok, hint in results:
        print(f"{'ok     ' if ok else 'MISSING'}  {name}" + ("" if ok else f" - add {hint}"))
    missing = sum(not ok for _, ok, _ in results)
    print(f"audit_report: {len(results) - missing} of {len(results)} parts present"
          + ("" if not missing else " - read and fill what is missing, check again, then reply with the report"))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
