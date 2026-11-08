# Testing `cia` — the fixture run

The skill's own S8 applies to the skill: a doctrine edit nobody has run is a written test, not a run one. This directory is the harness. It is deliberately small — a run takes an agent 20–40 minutes at Screen tier — so it can be run after **every** change to `SKILL.md` or `references/`.

## What is here

```
fixture-service/         a Python job runner with 12 planted defects and 8 verified controls
EXPECTED-fixture-service.md      the audit answer key: sweep, path:line, minimum grade — kept OUTSIDE the fixture on purpose
EXPECTED-build-fixture.md        the build-mode answer key: the artefacts §0.10a must produce, in order
RUNS.md                    one row per run (append; never rewrite history)
harness/cold_run.py        launches one cold run (audit | build | run-tests) on a throwaway copy of the fixture; prompts are read from this file
```

## Procedure

1. **Fresh session.** Open a new Claude Code (or Codex) session with `tests/fixture-service` as the working directory, or run `python tests/harness/cold_run.py --mode audit`. No project memory, no CLAUDE.md — the fixture must be audited cold, the way a new project would be.
2. **Trigger.** Say exactly: `pre-launch audit, Screen tier`. Separately, in another fresh session, say `run tests` alone: the expected behaviour is the test run first (`Ran 8 tests … OK`) and a one-line offer of the audit — not the protocol. Two things are under test before any sweep runs: §0.3 commerce detection must report *none* and the discovery block must say so; and the run must declare its tier.
3. **Let it run.** Do not answer questions the skill should answer itself (§0.8). If it asks the owner for something the fixture contains, that is a finding against the skill — record it.
4. **Score against `EXPECTED-fixture-service.md`** (the scorer reads it; the auditor never does — it sits beside this file, outside the fixture, because two cold runs on 2026-09-19 leaked it through the S6 deferred-work grep the doctrine itself prescribes over `tests/`; an answer key inside the audited tree is a key the auditor will hit)**:**
   - **Hit** — the planted row is reported under the right sweep, with a `path:line` inside the cited range and a grade at or above the minimum.
   - **Near** — right site, wrong sweep or grade one level low. Counts half.
   - **Unanchored** — right defect, right sweep, grade at or above the floor, but no `path:line` inside the cited range (a symbol, a file or a concept named without its line). Counts half, like near, and is listed in its own column of the note, because it is a reporting defect (reporting.md §9, the promotion rule) and not a discovery one — the fix is different.
   - **Miss** — not reported, or reported only as a count with no path.
   - **False positive** — a finding at a site with no planted defect. List each; decide whether the fixture is wrong (fix the fixture and re-run) or the doctrine is (fix the doctrine).
   - **Control misfiled** — a verified control reported as a defect. Counts as a miss.
   - **Vacuous line** — a sweep line with a count but no paths, or paths but no quoted line (§0.9). Counts as a miss for that sweep even if the finding was elsewhere reported.
5. **Record** a row in `RUNS.md`: date, commit of the skill, runtime (Claude / Codex), tier, hits / near / miss / false positives, minutes, and the one sentence that explains any miss.
6. **Gate for the change** (`python tools/score.py --gate`; installed as a pre-push hook by `tools/install-hooks.sh`). A change to the skill ships only if the run scores **no worse** — precisely: a change ships when every run on its commit has no miss and no false positive, and the mean of at least two runs is within half a row of the best earlier per-commit mean on the same fixture and model. Half a row is a reporting slip (near, unanchored) and is the instrument's noise; a miss is doctrine and is never noise. A new miss is a regression in the doctrine or in the packaging (the agent did not read the reference file) — find which before committing.

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

## The build-mode run

Everything above scores the skill answering *"is this wrong?"*. §0.10a answers *"write it"*, and a
build contract nobody has run cold is a written test, not a run one. The prompt — the first fenced
block here is what `tests/harness/cold_run.py --mode build` sends, so it holds the prompt and
nothing else:

```
build mode: make the job claim in runner/scheduler.py race-free and crash-safe, production-ready
```

1. **A throwaway copy, never the repo copy.** A build changes code, and the planted defects under
   `tests/fixture-service/` are what every audit row above is scored against; a build that lands
   on the repo copy repairs defect 3 and invalidates the audit key. `cold_run.py --mode build`
   copies the fixture to a fresh temp directory and runs there. Run by hand, do the same
   (`cp -r tests/fixture-service <tmp>`), and nothing from the copy comes back.
2. **The same HARD RULES** as every cold run: no `tests/EXPECTED-*.md`, no `tests/RUNS.md`, no
   `tests/corpus/entries/`; `references/*.md` read in full.
3. **Score against `EXPECTED-build-fixture.md`.** It scores the *artefacts* — obligation row before
   code, four proofs red before the implementation, output pasted, ledger row from the artefact,
   OBL id in the test names, line 14, the fixture suite still green, the closure gate counted — not
   whether the SQL ends up right. Correct code with no proof behind it misses every proof row. A
   verified control "fixed" along the way is a false positive, as in the audit key.
4. **Record** a row in `RUNS.md`'s build table (the section headed `## Build-mode runs`, at the end
   of the file; `tools/score.py` reads it separately so a build score can never move the audit
   gate). Same columns as the audit table; the Prompt cell holds the prompt above; the Note names
   any collateral edit outside `claim_batch` and the reason the run gave for it.
5. **The gate.** A miss here is **not a push blocker until a baseline row exists** — the first
   scored build run is recorded, not blocked, and `score.py --gate` compares later build rows
   against it on the same model. Until a row scores clean (no miss, no false positive),
   `README.md` and `SKILL.md` must **not** claim build mode is cold-tested; they may say the audit
   is, because it is.

## The corpus run — ground truth nobody planted

Everything above scores the skill against defects its own author wrote for it to find, which is
close to a tautology. `tests/corpus/` is the answer: real repositories, checked out at the commit
**before** a maintainer's own fix commit, with that commit's diff as the oracle.

```
python tests/corpus/run.py list
python tests/corpus/run.py prepare <entry>     # clone at the pre-fix commit; prints the path
python tests/corpus/run.py oracle <entry>      # SCORER ONLY - never shown to a run
```

Audit the prepared path cold, at the tier the entry names, then score one question: **did the run
report the thing the next commit had to fix, for the reason the commit gives?** Record HIT, MISS
or OUT-OF-SCOPE in `RUNS.md`'s corpus table.

Three rules keep it honest: the auditor never reads `tests/corpus/`; the fix commit is the
oracle rather than anybody's reading of the code; and a miss is recorded rather than explained
away, because a miss here is the doctrine's blind spot showing itself on real code. An entry that
keeps missing is the most valuable row in the harness.

## Blind-forward validation — the mode with no oracle

The corpus above has a bias it cannot remove by growing: **every entry is a commit whose author
had already diagnosed the bug and written its name in the subject line.** The auditor never sees
that message, but the defect had still been characterised by somebody before the audit began, and
the entry was chosen *because* it had been. It measures recall on named defect classes, which is
worth measuring and is not the same as finding something nobody knew about.

`tests/corpus/forward.py` removes the chooser:

```
python tests/corpus/forward.py pick <repo-url> --back 220
   ... audit the printed path, cold, and write the findings down ...
python tests/corpus/forward.py confirm <name> --files a.ts,b.ts
```

`pick` checks a repository out at a commit well back along its first-parent chain and prints the
path and nothing else — no subject, no date, no diff, nothing about what came next. **No oracle
exists at audit time.** `confirm` then replays the project's own future: every later commit that
touched the files the audit named.

| Verdict | Meaning |
|---|---|
| **CONFIRMED-BY-FUTURE** | a later commit changes the exact thing the finding named, for the reason the finding gave. The maintainers agreed, months later, knowing nothing about this skill |
| **OPEN** | nobody has touched it. **Not a miss** — the defect may well still be there, and an audit running ahead of its project is the thing you want |
| **WRONG** | a later commit shows the finding was mistaken about the code |

This is the only measurement in the harness that can register a defect **nobody had collected**,
which is the ceiling the retrospective corpus cannot reach by any amount of growth. It is also
the only one where `OPEN` is an honest outcome rather than a hole, so read the three verdicts
together and never quote a hit rate from this table alone.

**The rule that keeps it worth anything: step two happens between the other two.** Running
`confirm` before the audit is written down is reading an answer key — one that did not exist
until you looked. The audit prompt says so, and it also forbids the auditor from running `git`
at all inside the snapshot, because the history is right there and one `git log` would end the
measurement.

### The hard rule in the prompt fences the oracle, not the doctrine

Three cold runs on 2026-09-24 opened their reports by saying they had worked from `SKILL.md`
alone, because the prompt told them not to read anything under the skills directory - and
`references/` lives there. They were right to say so, and the receipts line is why it was
visible rather than mistaken for a doctrine gap. But every one of those runs was weaker than it
needed to be, and the prompt caused it.

**What the run must not read** is the answer: `tests/corpus/entries/`, `tests/EXPECTED-*.md`,
`tests/RUNS.md`, and - in a blind-forward run - the repository's own future, which means no
`git` command at all inside the snapshot.

**What the run must read** is the doctrine: `references/*.md`, in full, per §0.13.

So phrase it as a fence around the oracle:

```
HARD RULES:
- Do not read `tests/corpus/entries/`, `tests/EXPECTED-*.md` or `tests/RUNS.md` - those hold
  the scorer's answer key.
- (blind-forward only) Do not run any `git` command and do not read `.git/`. The snapshot sits
  in the middle of the project's history on purpose; one `git log` ends the measurement.
- You MAY and SHOULD read the skill's own `references/*.md`. They are your instructions, not
  part of the audited project.
```

A run that cannot quote the receipts is a run that worked from the index. If the prompt caused
that, the prompt is the finding.

## Reading a miss

| Symptom | Usually means |
|---|---|
| Sweep line present, path absent | agent read the §0.9 index and not `references/sweeps/` — packaging |
| Right site, wrong sweep | taxonomy wording; the two sweeps' boundaries are unclear in `sweeps/` |
| Control filed as defect | the §11 "verified controls" habit is not binding enough in `reporting.md` |
| Asked the owner for the architecture document | §1.4 / §0.5 discovery did not look under `docs/` |
| Line 14 `n/a` with surfaces on the map | the run skipped or overrode the ROUTE block — packaging |
| Reported tier but ran deeper or shallower | the tier table in Step 2 is not shaping the run |

## Paired run

Once per release of either skill, run this fixture with `run /cia and /ecommerce-cia, Screen tier`. Expected here (non-commerce): this skill is the spine, `ecommerce-cia` reports no gateway, no commerce schema and no checkout route in one line, and no commerce doctrine appears in the report. The commerce-side paired run lives in `../../ecommerce-cia/tests/RUNBOOK.md`. Record it as a separate row with runtime `paired`.
