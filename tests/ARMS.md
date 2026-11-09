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

**cia at the same time.** The first draft of this file compared the arms with runs K and L
(`c8ac18a`, 12 each, early on 2026-11-09). That was the wrong baseline: nine cia runs made within
the same hour as the arms, on the same doctrine (`c8ac18a`, or `889c473` = it plus one reverted
sentence), scored 9.5, 7, 8, 10.5, 10, 7, 3, 9, 8 (`RUNS.md`, runs O-W). Only three of the nine read
the references; the other six worked from SKILL.md and one to three sweep files.

## What the first comparison says (2026-11-09, same hour, same model)

| | runs | mean score (of 12) | misses per run | read the skill |
|---|---|---|---|---|
| no skill | 2 | 2.25 | 3.5 | n/a |
| ponytail-audit | 2 | 6.5 | 2 | n/a |
| cia, runs that skipped the references | 6 | 7.1 | 1.5 | no |
| cia, runs that read them | 3 | 9.8 | 0.3 | yes |
| cia, this morning (K, L) | 2 | 12 | 0 | yes |

- **cia's lead is its references.** A cia run that skips them scores about what ponytail scores;
  one that reads them leads by three rows. On this model, runs read them one time in three. That is
  now the skill's most important open defect (`RUNS.md` note of 2026-11-09, "the reading collapse").
- **Both rival arms miss the same two rows every time:** 5, the dead watchdog (a heartbeat nothing
  reads and no outermost check), and 9, the vacuous pass (a test asserting emptiness with no sibling
  proving non-emptiness). Those are S20 and S21: doctrine cia teaches and neither arm has. This is the measured
  reason to keep them.
- **Ponytail finds the sites as well as cia does** on the defects it reports, and anchors them
  well; it loses on grading (row 12 and row 4 as *Should fix*) and on the two rows above.
- **The cost side.** Arm runs took under two minutes; today's cia runs took 89-221 seconds (the
  header's `seconds`), the reading runs the longest. From `c4ac613` the header also carries the
  model that answered, the cost in dollars and the turns, so the next pair compares cost directly.
- **Not measured here:** a recurring false-positive rate (none of the four runs misfiled a control),
  and any other fixture. One fixture of twelve rows is a small sample; read the gap, not the decimal.
