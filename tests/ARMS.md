# Comparison arms: cia against no skill and against ponytail-audit

Does cia earn its tokens? The same audit task (`pre-launch audit, Screen tier` on `fixture-service`,
the same HARD RULES and permission line) run with the skill swapped out, through
`python tests/harness/cold_run.py --mode audit --arm none|ponytail --model sonnet`, scored against
`EXPECTED-fixture-service.md`. These rows never feed `tools/score.py`'s gate: they measure the
baseline, not the doctrine under test. `tools/due.py` says when a new pair is due.

## How an arm is scored (differs from RUNS.md in two places, both in the arm's favour)

- **No sweep.** An arm has no sweep vocabulary, so "right sweep" is not asked. A hit is the planted
  defect, a `path:line` inside the cited range (a file-only site: the file), and a grade at the floor.
- **Grades by rank.** The arm's top tier (ponytail *Must fix*, a bare run's *High*) counts as
  CRITICAL or HIGH; its second tier (*Should fix*, *Medium*) as MEDIUM; its third as LOW. A bare
  run that never uses CRITICAL is not marked down on row 3 for it, which a cia run would be.
- Near, unanchored, miss and false positive as in the RUNBOOK. A finding both a grade low **and**
  unanchored is a miss: neither half-credit rule covers it.
- A row whose header says anything but `cia-traces none` is void (the run reached the skill).

| Date | Skill commit | Arm | Model | Hits | Near | Unanch. | Miss | False+ | Score | Seconds | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-11-09 | `23d0128` | none | sonnet | 3 | 3 | 3 | 3 | 0 | 3.0 | <120 | Ran nothing. Misses: 5 heartbeat file named without the outermost check, Medium, no line; 9 vacuous pass absent; 10 env leak Low, no line. Rows 1, 7, 8 unanchored (`monitor.py:9`, `legacy_retry.with_backoff`). |
| 2026-11-09 | `23d0128` | none | sonnet | 3 | 2 | 3 | 4 | 0 | 1.5 | <120 | Ran nothing. Misses: 5, 9 (absent), 12 identity Medium with no line, 10 Low with no line. |
| 2026-11-09 | `23d0128` | ponytail | sonnet | 7 | 1 | 2 | 2 | 0 | 6.5 | <120 | Ran nothing. Misses: 5 heartbeat file as a Nice-to-have lean cut, 9 named only as "the only stuck test expects an empty list" under Should, no line. |
| 2026-11-09 | `23d0128` | ponytail | sonnet | 7 | 2 | 1 | 2 | 0 | 6.5 | <120 | Ran nothing. Misses: 5 (heartbeat as a crash-after-commit Nice), 9 absent. Finding 16 suggests deleting `cancel`'s first SELECT at control C4 and says the UPDATE guards: a lean note, not a misfiled control. |

**cia at the same time:** `c8ac18a`, runs K and L, 12 / 0 / 0 / 0 each (mean 12), with the live probe fired; their duration was not recorded
(`RUNS.md` Minutes cell: n/r).

## What the first comparison says (2026-11-09)

| | mean score (of 12) | misses per run | ran the code |
|---|---|---|---|
| no skill | 2.25 | 3.5 | no |
| ponytail-audit | 6.5 | 2 | no |
| **cia** | **12** | **0** | yes (`RUNS.md` runtime table) |

- **Both rival arms miss the same two rows every time:** 5, the dead watchdog (a heartbeat nothing
  reads and no outermost check), and 9, the vacuous pass (a test asserting emptiness with no sibling
  proving non-emptiness). Those are S20 and S21: doctrine cia teaches and neither arm has. This is the measured
  reason to keep them.
- **Ponytail finds the sites as well as cia does** on the defects it reports, and anchors them
  well; it loses on grading (row 12 and row 4 as *Should fix*) and on the two rows above.
- **The cost side is not measured yet.** Each arm run finished within two minutes of its launch;
  cia's runs never recorded a duration. Every report header carries `seconds` from now on, so the
  next cia pair and the next arm pair settle what cia costs for its six points.
- **Not measured here:** a recurring false-positive rate (none of the four runs misfiled a control),
  and any other fixture. One fixture of twelve rows is a small sample; read the gap, not the decimal.
