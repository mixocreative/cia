# Testing `cia` — the fixture run

The skill's own S8 applies to the skill: a doctrine edit nobody has run is a written test, not a run one. This directory is the harness. It is deliberately small — a run takes an agent 20–40 minutes at Screen tier — so it can be run after **every** change to `SKILL.md` or `references/`.

## What is here

```
fixture-service/         a Python job runner with 10 planted defects and 2 correct controls
EXPECTED-fixture-service.md      the answer key: sweep, path:line, minimum grade — kept OUTSIDE the fixture on purpose
RUNS.md                    one row per run (append; never rewrite history)
```

## Procedure

1. **Fresh session.** Open a new Claude Code (or Codex) session with `tests/fixture-service` as the working directory. No project memory, no CLAUDE.md — the fixture must be audited cold, the way a new project would be.
2. **Trigger.** Say exactly: `pre-launch audit, Screen tier`. Separately, in another fresh session, say `run tests` alone: the expected behaviour is the test run first (`Ran 4 tests … OK`) and a one-line offer of the audit — not the protocol. Two things are under test before any sweep runs: §0.3 commerce detection must report *none* and the discovery block must say so; and the run must declare its tier.
3. **Let it run.** Do not answer questions the skill should answer itself (§0.8). If it asks the owner for something the fixture contains, that is a finding against the skill — record it.
4. **Score against `EXPECTED-fixture-service.md`** (the scorer reads it; the auditor never does — it sits beside this file, outside the fixture, because two cold runs on 2026-09-19 leaked it through the S6 deferred-work grep the doctrine itself prescribes over `tests/`; an answer key inside the audited tree is a key the auditor will hit)**:**
   - **Hit** — the planted row is reported under the right sweep, with a `path:line` inside the cited range and a grade at or above the minimum.
   - **Near** — right site, wrong sweep or grade one level low. Counts half.
   - **Miss** — not reported, or reported only as a count with no path.
   - **False positive** — a finding at a site with no planted defect. List each; decide whether the fixture is wrong (fix the fixture and re-run) or the doctrine is (fix the doctrine).
   - **Control misfiled** — a verified control reported as a defect. Counts as a miss.
   - **Vacuous line** — a sweep line with a count but no paths, or paths but no quoted line (§0.9). Counts as a miss for that sweep even if the finding was elsewhere reported.
5. **Record** a row in `RUNS.md`: date, commit of the skill, runtime (Claude / Codex), tier, hits / near / miss / false positives, minutes, and the one sentence that explains any miss.
6. **Gate for the change** (`python tools/score.py --gate`; installed as a pre-push hook by `tools/install-hooks.sh`). A change to the skill ships only if the run scores **no worse** than the previous row on hits and misses. A new miss is a regression in the doctrine or in the packaging (the agent did not read the reference file) — find which before committing.

## The live probe (`fixture-service`, no second fixture needed)

`cia`'s fixture is already runnable — it is a Python job runner with a sqlite database — and its
S2 site (two workers claiming one job) is a planted defect that the read audit can only
*predict*. `browser-walks.md` §13 says a prediction on a system that is running on this machine
is evidence left on the floor, so the harness scores whether the auditor fired it:

1. Seed one queued job.
2. Start two claim processes against it concurrently — two shells, `python -c` against
   `runner.scheduler`, or the service's own entry point twice.
3. Read the job row afterwards.

Expected, given the planted defect: **both claim it**. An auditor that reports the race CRITICAL
*and* fires the probe scores the finding and the runtime credit; one that reports it without
firing scores the finding alone; one that fires it and finds the divergence undetected by any
monitor has also just earned the S20 row for free. Record the probe in the RUNS runtime table
(`probes`), with the two outputs as its artefact.

The same three runtime columns apply here as in the commerce harness: ladders run (the primary
quantity in this service is the claim on a job), probes fired, and whether an evidence ledger
was produced with artefact paths on every PASS.

## Reading a miss

| Symptom | Usually means |
|---|---|
| Sweep line present, path absent | agent read the §0.9 index and not `references/sweeps.md` — packaging |
| Right site, wrong sweep | taxonomy wording; the two sweeps' boundaries are unclear in `sweeps.md` |
| Control filed as defect | the §29 "verified controls" habit is not binding enough in `reporting.md` |
| Asked the owner for the architecture document | §1.4 / §0.5 discovery did not look under `docs/` |
| Reported tier but ran deeper or shallower | the tier table in Step 2 is not shaping the run |

## Paired run

Once per release of either skill, run this fixture with `run /cia and /ecommerce-cia, Screen tier`. Expected here (non-commerce): this skill is the spine, `ecommerce-cia` reports no gateway, no commerce schema and no checkout route in one line, and no commerce doctrine appears in the report. The commerce-side paired run lives in `../../ecommerce-cia/tests/RUNBOOK.md`. Record it as a separate row with runtime `paired`.
