#!/usr/bin/env python3
"""The skill's own score, read from tests/RUNS.md - and the gate the RUNBOOK states in prose.

    python tools/score.py            # print the newest scored row as one line
    python tools/score.py --gate     # exit 1 when the newest row scores below the row before it
    python tools/score.py --badge    # a Markdown badge line for the README
    python tools/score.py --runtime  # print the newest runtime row (what the run RAN, not found)
    python tools/score.py --corpus   # the corpus table: ground truth nobody planted

A doctrine change ships only if the fixture run scores no worse than the last one (RUNBOOK
step 6). Written down, that rule was skipped the first day seven edits landed before the run
started; a rule a hook can run is a rule that holds (S8: a written test is not a run test).
The score is hits minus misses, on the same fixture; "near" counts half and a false positive
counts against. Rows with no numbers (the placeholder row) are ignored.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# CIA_RUNS lets a test point the scorer at synthetic text instead of the real ledger.
RUNS = Path(os.environ.get("CIA_RUNS") or
            Path(__file__).resolve().parent.parent / "tests" / "RUNS.md")

# Build-mode runs live in their own table at the END of RUNS.md. The trap: the build table has the
# same columns as the fixture table, so a reader that only checks "| 20" and the cell count would
# take a build row for an audit row and let a build score move (or hide) the audit gate. Every
# audit reader therefore stops at this heading, and only build_rows() reads past it.
BUILD_HEADING = "## Build-mode runs"


def runtime_rows() -> list[dict]:
    """Rows of the second table in RUNS.md: what a run executed, not what it found.

    Added 2026-09-24. The first table scores reading; a doctrine that asks for ladders, probes
    and an evidence ledger and never measures them is scoring the half that was easy to score.
    """
    text = RUNS.read_text(encoding="utf-8")
    if "## Runtime evidence" not in text:
        return []
    out = []
    section = text.split("## Runtime evidence", 1)[1]
    section = section.split(chr(10) + "## ", 1)[0]   # stop at the next heading, not at EOF
    for line in section.splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7:
            continue
        try:
            unproved = int(re.match(r"\d+", cells[6]).group())
        except (AttributeError, ValueError):
            continue
        out.append({
            "date": cells[0], "fixture": cells[1], "ladders": cells[2],
            "adversarial": cells[3], "probes": cells[4], "ledger": cells[5],
            "pass_without_artefact": unproved,
        })
    return out


RUNTIME_SINCE = "2026-09-24"


def model_of(runtime: str) -> str:
    """Which model produced a row. A doctrine regression is a drop against the same one.

    Added 2026-09-24, when the first Sonnet rows made both gates fail by being compared against
    Opus rows on the same fixture - a model comparison wearing a regression's clothes.
    """
    low = runtime.lower()
    # The model that actually answered, when the row records it (cold_run.py's header, from c4ac613).
    # Added 2026-11-09: one doctrine scored 12, 12 at dawn and 3-10.5 by late morning under the same
    # `sonnet` alias, CLI unchanged, every harness variable ruled out by experiment. An alias is not a
    # model; pooling rows across what it resolved to is the Opus-vs-Sonnet trap above, unrecorded.
    # Rows without the id stay under the alias, since nobody can say what answered them.
    m = re.search(r"resolved (claude-[a-z0-9-]+)", low)
    if m:
        return m.group(1)
    if "paired" in low:
        return "paired"
    for name in ("opus", "sonnet", "haiku", "fable", "codex", "gpt"):
        if name in low:
            return name
    if "live" in low:
        return "live"
    return "unknown"


CHEAP = ("sonnet", "haiku")


def is_cheap(model: str) -> bool:
    """A resolved id (claude-sonnet-5-5) is as cheap as its alias; matching the tuple exactly called it dear."""
    return any(name in model for name in CHEAP)


def corpus_rows() -> list[dict]:
    """Rows of the corpus table: real repositories, audited at the commit before a real fix.

    Added 2026-09-24. The fixture score measures whether the skill finds defects its own author
    planted, which is close to a tautology. These rows measure whether it finds a defect a
    maintainer had to fix, chosen by somebody else, in code nobody wrote for this harness.
    """
    text = RUNS.read_text(encoding="utf-8")
    if "## Corpus" not in text:
        return []
    out = []
    section = text.split("## Corpus", 1)[1]
    section = section.split(chr(10) + "## ", 1)[0]   # stop at the next heading; the cost table is not the corpus
    for line in section.splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        out.append({"date": cells[0], "entry": cells[1],
                    "verdict": cells[2].upper().strip("* "),
                    "note": cells[-1]})
    return out


def fixture_of(tier: str) -> str:
    """Which harness a row was scored on.

    Added 2026-09-24 with the live fixture. The gate compares like with like: a run on a
    runnable shop and a run on a source tree measure different things, and comparing their
    scores would either block an honest first baseline or hide a real regression behind a
    higher number from the other harness. The RUNS row names its fixture in the tier cell.
    """
    low = tier.lower()
    # Longest first: "fixture-shop-node" contains "fixture-shop", and matching the shorter one
    # compared the node fixture against the read fixture's history on the day it was added.
    for name in ("fixture-shop-live", "fixture-shop-node", "fixture-service", "fixture-shop"):
        if name in low:
            return name
    return "default"


def commit_of(cell: str) -> str:
    """The skill commit a row measured: the first backticked hex token, else the whole cell."""
    m = re.search(r"`([0-9a-f]{7})[0-9a-f]*`", cell)
    return m.group(1) if m else cell.strip()


# Half a row: one near or unanchored slip, the smallest unit the answer key scores. Six sonnet rows on
# fixture-service read 11, 12, 12, 10.5, 11.5, 11.5 - the instrument's noise is about this size, and
# every half-row so far was a reporting slip, never a discovery miss.
NOISE = 0.5


def audit_gate(rs: list[dict]) -> int:
    """Per-commit gate. Misses and false positives are doctrine: zero tolerance. Half-rows are noise:
    the mean of at least two runs on the commit under test must stay within NOISE of the best earlier
    per-commit mean, and that floor is taken against the best ever, so it can never drift down."""
    live = [r for r in rs if not r.get("reverted")]
    if not live:
        print("gate: every scored run is on a reverted commit - nothing under test.")
        return 0
    last = live[-1]
    # Debt, known: this pools launcher (cold_run.py) rows with cold-subagent rows. ecommerce-cia split them
    # on 2026-11-09 (instrument_of), where the launcher measured half a row under a subagent on one doctrine.
    # Here both instruments have scored 12 on fixture-service, so the split is not taken; take it if they diverge.
    pool = [r for r in rs if r["fixture"] == last["fixture"] and r["model"] == last["model"]]
    group = [r for r in pool if r["token"] == last["token"]]
    earlier = [r for r in pool if r["token"] != last["token"]]
    # The miss rule asks whether the fixture's rows are findable at all, which any model's clean run
    # proves; it is not a score comparison, so it is neither pooled by model nor skipped for a model's
    # first commit. Either let a new model's first commits through with misses.
    findable = [r for r in rs if r["fixture"] == last["fixture"] and r["token"] != last["token"]]
    if any(r["miss"] == 0 and r["false"] == 0 for r in findable):
        dirty = [r for r in group if r["miss"] or r["false"]]
        if dirty:
            r = dirty[-1]
            print(f"GATE: a run on {last['token']} has {r['miss']} miss / {r['false']} false positive, on a fixture "
                  f"where an earlier run had none. A miss is doctrine, never noise (RUNBOOK step 6).", file=sys.stderr)
            return 1
    if not earlier:
        print(f"gate: {last['token']} is the first scored commit on {last['fixture']} with {last['model']} - "
              f"a baseline, nothing to compare it against. Recorded, not blocked.")
        return 0
    if len(group) < 2:
        print(f"GATE: {last['token']} has one scored run on {last['fixture']} with {last['model']}. One run is a "
              f"sample - run again, then gate on the mean (RUNBOOK step 6).", file=sys.stderr)
        return 1
    means: dict[str, list[float]] = {}
    for r in earlier:
        means.setdefault(r["token"], []).append(r["score"])
    best = max(sum(v) / len(v) for v in means.values())
    mean = sum(r["score"] for r in group) / len(group)
    if mean < best - NOISE:
        print(f"GATE: {last['token']} scores a mean of {mean:g} over {len(group)} runs, below the floor "
              f"{best - NOISE:g} (best earlier per-commit mean {best:g}, less half a row). Fix the doctrine or "
              f"the fixture, run again, then push.", file=sys.stderr)
        return 1
    print(f"gate: {last['token']} mean {mean:g} over {len(group)} runs, floor {best - NOISE:g} "
          f"(best earlier per-commit mean {best:g}); no miss, no false positive.")
    return 0


def _parse(lines) -> list[dict]:
    """Shared cell parsing for the audit table and the build table (same column positions)."""
    out = []
    for line in lines:
        if not line.startswith("| 20"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 9:
            continue
        try:
            hits = int(re.match(r"\d+", cells[4]).group())
            near = int(re.match(r"\d+", cells[5]).group())
            miss = int(re.match(r"\d+", cells[6]).group())
            false = int(re.match(r"\d+", cells[7]).group())
        except (AttributeError, ValueError):
            continue
        out.append({
            "date": cells[0], "commit": cells[1][:40], "tier": cells[3][:60],
            "hits": hits, "near": near, "miss": miss, "false": false,
            "score": hits + 0.5 * near - miss - false,
            "fixture": fixture_of(cells[3]),
            "model": model_of(cells[2]),
            "token": commit_of(cells[1]),
            # A row whose commit cell says "reverted" measured doctrine that no longer ships: it stays in the
            # history and in the floor, but it is never the commit under test.
            "reverted": "reverted" in cells[1].lower(),
        })
    return out


def rows() -> list[dict]:
    """Audit (fixture) rows: everything BEFORE the build-mode heading, never after it."""
    text = RUNS.read_text(encoding="utf-8")
    return _parse(text.split(BUILD_HEADING, 1)[0].splitlines())


def build_rows() -> list[dict]:
    """Build-mode rows: only those after the build-mode heading. Placeholder dash rows drop out
    in _parse (no integers), so "no scored build run yet" is simply an empty list."""
    text = RUNS.read_text(encoding="utf-8")
    if BUILD_HEADING not in text:
        return []
    section = text.split(BUILD_HEADING, 1)[1]
    section = section.split(chr(10) + "## ", 1)[0]
    return _parse(section.splitlines())


def line(r: dict) -> str:
    return (f"{r['date']} {r['commit']}: hits {r['hits']} / near {r['near']} / miss {r['miss']} / "
            f"false+ {r['false']} -> score {r['score']:g}")


def build_gate(bs: list[dict]) -> int:
    """Newest build row against the best earlier build row on the same model. Same rule as audit."""
    if not bs:
        return 0   # main() has already printed "build: no scored build run yet"
    # Same rule as audit_gate: a row on a reverted commit measured doctrine that no longer ships.
    live = [r for r in bs if not r.get("reverted")]
    if not live:
        return 0
    last = live[-1]
    same = [r for r in bs if r is not last and r["model"] == last["model"] and bs.index(r) < bs.index(last)]
    if not same:
        print(f"build gate: {last['date']} is the first scored build run with {last['model']} - "
              f"a baseline. Recorded, not blocked.")
        return 0
    prev = max(same, key=lambda r: (r["score"], -r["miss"]))  # ratchet: a recorded regression never becomes the baseline
    if last["score"] < prev["score"] or last["miss"] > prev["miss"]:
        print(f"GATE: the newest build run with {last['model']} ({last['score']:g}, {last['miss']} miss) "
              f"scores below the best earlier build run with the same model ({prev['date']}: "
              f"{prev['score']:g}, {prev['miss']} miss).", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    rs = rows()
    if not rs:
        print("score: no scored run in tests/RUNS.md - the gate has nothing to hold", file=sys.stderr)
        return 1
    if "--badge" in argv:
        r = rs[-1]
        print(f"**Last scored fixture run:** {r['date']} - {r['hits']} hits / {r['near']} near / "
              f"{r['miss']} miss / {r['false']} false positives (`python tools/score.py`)")
        return 0
    rt = runtime_rows()
    if "--runtime" in argv:
        if not rt:
            print("runtime: no runtime-scored run in tests/RUNS.md - the running half is unmeasured",
                  file=sys.stderr)
            return 1
        r = rt[-1]
        print(f"runtime: {r['date']} {r['fixture']}: ladders {r['ladders']} / adversarial {r['adversarial']} / "
              f"probes {r['probes']} / ledger {r['ledger']} / PASS without artefact {r['pass_without_artefact']}")
        return 0

    print(f"score: [{rs[-1]['fixture']} / {rs[-1]['model']}] " + line(rs[-1]))

    # A doctrine that scores well only on the expensive model works on one budget. Say the cheap
    # number next to the expensive one, every time, so the gap is never invisible.
    cheap = [r for r in rs if is_cheap(r["model"])]
    if cheap:
        c = cheap[-1]
        dear = [r for r in rs if r["fixture"] == c["fixture"] and not is_cheap(r["model"]) and r["model"] != "unknown"]
        gap = f", against {dear[-1]['score']:g} on {dear[-1]['model']}" if dear else ""
        print(f"cheap model: {c['date']} [{c['fixture']} / {c['model']}] scored {c['score']:g}{gap}")

    cr = corpus_rows()
    if "--corpus" in argv:
        if not cr:
            print("corpus: no entries scored yet - the ground truth nobody planted is still empty,"
                  " and an empty corpus proves nothing (tests/corpus/README.md)", file=sys.stderr)
            return 1
        hits = sum(1 for r in cr if r["verdict"].startswith("HIT"))
        print(f"corpus: {hits} hit / {len(cr) - hits} other, of {len(cr)} scored entries")
        for r in cr:
            print(f"  {r['date']}  {r['verdict']:12} {r['entry']}")
        return 0
    if cr:
        hits = sum(1 for r in cr if r["verdict"].startswith("HIT"))
        print(f"corpus: {hits}/{len(cr)} real fix commits found before the fix")
    if rt:
        r = rt[-1]
        print(f"runtime: {r['date']} {r['fixture']}: ladders {r['ladders']} / probes {r['probes']} / "
              f"ledger {r['ledger']} / PASS without artefact {r['pass_without_artefact']}")

    bs = build_rows()
    if bs:
        b = bs[-1]
        print(f"build: [{b['model']}] " + line(b))
    else:
        print("build: no scored build run yet")

    if "--gate" in argv:
        if bs and build_gate(bs):
            return 1
        if audit_gate(rs):
            return 1

        # A PASS the run cannot point at is the one thing the evidence ledger forbids
        # (reporting.md). It is scored as a false positive and it blocks the push.
        bad = [r for r in rt if r["pass_without_artefact"] > 0]
        if bad:
            r = bad[-1]
            print(f"GATE: the runtime row of {r['date']} carries {r['pass_without_artefact']} ledger PASS row(s) with "
                  f"no artefact. Reading never produces PASS (reporting.md, the evidence ledger). Either the artefact "
                  f"exists and is uncited, or the row is UNVERIFIED.", file=sys.stderr)
            return 1

        # From RUNTIME_SINCE on, a scored run with nothing recorded about what it executed is a
        # code review, and the harness says so instead of quietly scoring half the doctrine.
        newest = rs[-1]
        if newest["date"] >= RUNTIME_SINCE and not any(r["date"] == newest["date"] for r in rt):
            print(f"GATE: the scored run of {newest['date']} has no row in the runtime table. Since {RUNTIME_SINCE} a "
                  f"run also records what it RAN - ladders, adversarial rows, probes, ledger (RUNBOOK, the live "
                  f"fixture run). Add the row, or record it as a code review.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
