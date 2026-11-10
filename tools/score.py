#!/usr/bin/env python3
"""The skill's own score, read from tests/RUNS.md - and the gate the RUNBOOK states in prose.

    python tools/score.py            # print the newest scored row as one line
    python tools/score.py --gate     # exit 1 when the commit under test fails the gate (commit_gate below)
    python tools/score.py --badge    # a Markdown badge line for the README
    python tools/score.py --runtime  # print the newest runtime row (what the run RAN, not found)
    python tools/score.py --corpus   # the corpus table: ground truth nobody planted

A doctrine change ships only if its runs score no worse than what shipped before (RUNBOOK step 6:
the mean of two runs against a floor, no row every run missed, no false positive). Written down, that rule was skipped the first day seven edits landed before the run
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
    # A Codex row run at a reasoning effort other than the owner's default (`medium`, C1-C21) is its own
    # series: high effort read more and missed less (C22/C23), and pooling the two hides both trends.
    e = re.search(r"effort (\w+)", low)
    if "codex" in low and e:
        return f"codex-{e.group(1)}"
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


def corpus_current(rows: list[dict]) -> list[dict]:
    """The newest verdict per entry, leaving out entries not run (N/A: a deleted repository). Summing
    every row mixed two measurement dates into one rate (13/17 on 2026-11-10 for 7 of 8 that day)."""
    newest: dict[str, dict] = {}
    for r in rows:
        if r["verdict"].startswith("N/A"):
            continue
        if r["entry"] not in newest or r["date"] >= newest[r["entry"]]["date"]:
            newest[r["entry"]] = r
    return list(newest.values())


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
    for name in ("fixture-shop-live", "fixture-shop-node", "fixture-service", "fixture-editor", "fixture-shop"):
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
# The floor's baseline is the MEDIAN of the last RECENT live per-commit means, not the best ever. Changed
# 2026-11-09: "best ever" is the maximum of noisy two-run means, so it ratchets up on luck - one commit
# at 12 set a floor of 11.5 that commits scoring 11-12 on unchanged reading then failed about half the
# time (run AS, 11). The median does not chase the luckiest pair. The trap it opens is slow drift
# down, so DRIFT bounds it: the floor never sits more than one row (two slips) under the best ever.
# Misses and false positives stay zero-tolerance either way; this rule only sizes the noise.
RECENT = 5
DRIFT = 1.0
# Second stage: a two-run mean at most this far under the floor earns two more runs, once (RUNBOOK step 6).
# fixture-editor's two-run means spread about 0.6 around 10.4 for unchanged audit doctrine (2026-11-09), so a
# floor of 10 failed about one sound commit in four; four runs halve that spread. Never a third stage.
SECOND_STAGE = 1.0


def audit_gate(rs: list[dict]) -> int:
    return commit_gate(rs, "gate", every_fixture=True)


def commit_gate(rs: list[dict], name: str, every_fixture: bool = False) -> int:
    """Per-commit gate, for audit rows and build rows alike. Misses and false positives are doctrine:
    zero tolerance. Half-rows are noise: the mean of at least two runs on the commit under test must
    stay within NOISE of the median of the last RECENT live per-commit means, and never more than
    DRIFT under the best ever.

    every_fixture (the audit gate, since fixture-editor joined on 2026-11-09): the commit is judged on
    every fixture that has history before it, and a fixture it was never run on blocks it. Judging only
    the newest row's fixture let a doctrine change pass on one project while untested on the other."""
    live = [r for r in rs if not r.get("reverted")]
    if not live:
        print(f"{name}: every scored run is on a reverted commit - nothing under test.")
        return 0
    token = live[-1]["token"]
    # A commit is judged only against what was measured before it. After a revert the shipped commit is
    # the newest live one, and later reverted experiments must not raise its floor or its miss bar.
    first = next(i for i, r in enumerate(rs) if r["token"] == token)
    fixtures = {r["fixture"] for r in rs if r["token"] == token}
    if every_fixture:
        fixtures |= {r["fixture"] for r in rs[:first] if r["fixture"] != "default"}
    code = 0
    for fixture in sorted(fixtures):
        code |= _gate_one(rs, name, token, fixture, first)
    return code


def _gate_one(rs: list[dict], name: str, token: str, fixture: str, first: int) -> int:
    group_any = [r for r in rs if r["token"] == token and r["fixture"] == fixture]
    if not group_any:
        print(f"{name.upper()}: {token} has no scored run on {fixture}, which has history. A doctrine change "
              f"is run on every fixture before the push (RUNBOOK, 'The second fixture').", file=sys.stderr)
        return 1
    model = group_any[-1]["model"]
    # Debt, known: this pools launcher (cold_run.py) rows with cold-subagent rows. ecommerce-cia split them
    # on 2026-11-09 (instrument_of), where the launcher measured half a row under a subagent on one doctrine.
    # Here both instruments have scored 12 on fixture-service, so the split is not taken; take it if they diverge.
    pool = [r for r in rs if r["fixture"] == fixture and r["model"] == model]
    group = [r for r in pool if r["token"] == token]
    earlier = [r for r in rs[:first] if r in pool]
    # The miss rule asks whether the fixture's rows are findable at all, which any model's clean run
    # proves; it is not a score comparison, so it is neither pooled by model nor skipped for a model's
    # first commit. Only a clean run recorded BEFORE the commit under test makes its misses a regression:
    # a clean run on a later, reverted commit (build run 10, 2026-11-09) held the still-shipped commit to
    # a bar it was never measured against and blocked every push.
    findable = [r for r in rs[:first] if r["fixture"] == fixture]
    if any(r["miss"] == 0 and r["false"] == 0 for r in findable):
        blocking = doctrine_misses(group_any)
        if blocking:
            print(f"{name.upper()}: on {token}, {blocking} on {fixture}, where an earlier run had none. A miss the "
                  f"paired run did not make up for is doctrine, never noise (RUNBOOK step 6).", file=sys.stderr)
            return 1
    if not earlier:
        print(f"{name}: {token} is the first scored commit on {fixture} with {model} - "
              f"a baseline, nothing to compare it against. Recorded, not blocked.")
        return 0
    if len(group) < 2:
        print(f"{name.upper()}: {token} has one scored run on {fixture} with {model}. One run is a "
              f"sample - run again, then gate on the mean (RUNBOOK step 6).", file=sys.stderr)
        return 1
    if len(group) not in (2, 4):
        # Two runs, or four when the second stage applies: a commit is never sampled until it passes.
        print(f"{name.upper()}: {token} has {len(group)} scored runs on {fixture}. The gate reads two, or four "
              f"after one second stage (RUNBOOK step 6); a third stage is optional stopping.", file=sys.stderr)
        return 1
    best, baseline = floor_parts(earlier)
    floor = max(baseline - NOISE, best - DRIFT)
    mean = sum(r["score"] for r in group) / len(group)
    why = f"median of the last {RECENT} live per-commit means {baseline:g}, best ever {best:g}"
    if mean < floor:
        second = len(group) == 2 and floor - mean <= SECOND_STAGE
        print(f"{name.upper()}: {token} scores a mean of {mean:g} over {len(group)} runs on {fixture}, below the "
              f"floor {floor:g} ({why}). "
              + ("Within one row: run it twice more, once, and gate on the four-run mean (RUNBOOK step 6)."
                 if second else "Fix the doctrine or the fixture, run again, then push."), file=sys.stderr)
        return 1
    # Say what was checked: a row one run missed and its pair found passes (doctrine_misses), and
    # printing "no miss" over such a pair claimed more than the gate knows.
    misses = "no row missed by every run" if any(r["miss"] for r in group_any) else "no miss"
    print(f"{name}: {token} on {fixture}: mean {mean:g} over {len(group)} runs, floor {floor:g} ({why}); "
          f"{misses}, no false positive.")
    return 0


MISSED = re.compile(r"missed:\s*([^.;|*]+)", re.I)
ROW_ID = re.compile(r"row\s+\d+|#?\w+")   # `row 10`, `E8`, `#15`: what a key calls a row


def missed_of(note: str):
    """Row ids from a `missed: E8, row 10` tag in the note, as a set; None when there is no tag."""
    m = MISSED.search(note)
    if not m:
        return None
    # The id alone: `E8 (the overlap is noted, not filed)` and `E8` are one row. Compared as whole
    # strings, two runs that both missed it shared nothing, and the gate passed a row every run lost.
    # shortcut: a comma inside a parenthesis leaves a stray word as an id, which can only add a block.
    ids = (ROW_ID.match(x.strip().lower()) for x in m.group(1).split(","))
    return {" ".join(i.group().split()) for i in ids if i}


def doctrine_misses(group: list[dict]) -> str:
    """What blocks a commit: any false positive, an untagged miss, or a row EVERY run on it missed.

    Since 2026-11-09 a row one run missed and its paired run found is attention variance, not doctrine:
    the pair proves the doctrine finds it, and the miss still costs a row in the mean. Before that, one
    run's miss blocked the commit, and on fixture-editor rows a sound run finds seven times in nine
    (E8, E12) that made the gate a coin flip on a sound commit. A row lost by doctrine is lost by both
    runs, and that still blocks."""
    false = [r for r in group if r["false"]]
    if false:
        return f"a run has {false[-1]['false']} false positive"
    dirty = [r for r in group if r["miss"]]
    if not dirty:
        return ""
    if any(not r.get("missed") for r in dirty):   # no tag, or a tag naming no row: both are unreadable
        return f"a run has {dirty[-1]['miss']} miss with no `missed:` tag naming the rows"
    common = set.intersection(*[(r.get("missed") or set()) for r in group])
    return f"every run missed {', '.join(sorted(common))}" if common else ""


def floor_parts(earlier: list[dict]) -> tuple[float, float]:
    """(best per-commit mean ever, median of the last RECENT live per-commit means), in row order.

    Reverted commits count toward the best (a lucky pair on reverted doctrine still bounds drift) but
    not toward the median: the baseline is what the shipped doctrine scores."""
    means: dict[str, list[float]] = {}
    live: list[str] = []
    for r in earlier:
        means.setdefault(r["token"], []).append(r["score"])
        if not r.get("reverted") and r["token"] not in live:
            live.append(r["token"])
    avg = {t: sum(v) / len(v) for t, v in means.items()}
    best = max(avg.values())
    recent = sorted(avg[t] for t in live[-RECENT:]) or [best]
    mid = len(recent) // 2
    median = recent[mid] if len(recent) % 2 else (recent[mid - 1] + recent[mid]) / 2
    return best, median


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
            # The rows a run missed, when the scorer tags them in the note (`missed: E8, row 10`). None when
            # untagged: the paired-miss rule then cannot tell variance from doctrine and blocks.
            "missed": missed_of(cells[9]) if len(cells) > 9 else None,
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


OTHER_HEADING = "## Other runtimes"


def codex_rows() -> list[dict]:
    """Codex audit rows: the "Other runtimes" section only, gated against Codex's own history.

    Joined 2026-11-10 under the rule written when Codex was first measured: it joins once two Codex runs
    on one commit have no miss (C16, C17 on 798ee54). Never pooled with Claude's rows: Codex's means sat
    two rows under Claude's for the same doctrine, so pooling would make every Codex pair a regression."""
    text = RUNS.read_text(encoding="utf-8")
    if OTHER_HEADING not in text:
        return []
    section = text.split(OTHER_HEADING, 1)[1].split(chr(10) + "## ", 1)[0]
    return [r for r in _parse(section.splitlines()) if r["model"].startswith("codex") and r["fixture"] != "default"]


def codex_gate(cs: list[dict]) -> int:
    """The audit rule (commit_gate) over Codex rows: the newest live Codex commit, its own floor."""
    code = 0
    for m in sorted({r["model"] for r in cs}):   # one series per reasoning effort, never pooled
        code |= commit_gate([r for r in cs if r["model"] == m], f"codex gate [{m}]")
    return code


def line(r: dict) -> str:
    return (f"{r['date']} {r['commit']}: hits {r['hits']} / near {r['near']} / miss {r['miss']} / "
            f"false+ {r['false']} -> score {r['score']:g}")


def build_gate(bs: list[dict]) -> int:
    """Build rows under the audit rule (commit_gate): the mean of two runs on the commit, no miss once
    any build run was clean. Until 2026-11-09 this compared the newest single row with the best single
    row. Build run 10 then scored 9.5 against a best of 4, and that one row would have become the bar
    every later single run must beat: the lucky-best ratchet audit_gate shed the same day."""
    if not bs:
        return 0   # main() has already printed "build: no scored build run yet"
    return commit_gate(bs, "build gate")


FLAGS = ("--gate", "--badge", "--runtime", "--corpus")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    unknown = [a for a in argv[1:] if a not in FLAGS]
    if unknown:
        # The trap: flags are matched by `in argv`, so a mistyped --gate printed the score and exited 0,
        # which a hook reads as the gate passing.
        print(f"score: unknown argument {' '.join(unknown)}; known: {' '.join(FLAGS)}", file=sys.stderr)
        return 2
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
        cur = corpus_current(cr)
        hits = sum(1 for r in cur if r["verdict"].startswith("HIT"))
        print(f"corpus (newest verdict per entry): {hits} hit / {len(cur) - hits} other, of {len(cur)} entries run")
        for r in cr:
            print(f"  {r['date']}  {r['verdict']:12} {r['entry']}")
        return 0
    if cr:
        cur = corpus_current(cr)
        hits = sum(1 for r in cur if r["verdict"].startswith("HIT"))
        print(f"corpus: {hits}/{len(cur)} real fix commits found before the fix (newest run of each entry)")
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

    cs = codex_rows()
    if cs:
        print(f"codex: [{cs[-1]['fixture']}] " + line(cs[-1]))

    if "--gate" in argv:
        if bs and build_gate(bs):
            return 1
        if codex_gate(cs):
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
    if {"-h", "--help"} & set(sys.argv[1:]):   # answered here, before main(): --help must never run the job
        sys.stdout.reconfigure(encoding="utf-8")
        print(__doc__)
        sys.exit(0)
    sys.exit(main())
