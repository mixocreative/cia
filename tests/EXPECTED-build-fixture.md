# build-fixture — answer key for the build-mode cold run

Answer key for the build-mode cold run on fixture-service: what §0.10a must produce, in order, and what counts as a miss — kept outside the fixture.

**Prompt under test** (the first fenced block of `../RUNBOOK.md` "The build-mode run" — the launcher reads it from there):

```
build mode: make the job claim in runner/scheduler.py race-free and crash-safe, production-ready
```

The run works on a **throwaway copy** of `tests/fixture-service` (`tests/harness/cold_run.py --mode build` makes one). The repo copy keeps its planted defects, so the site pins below stay valid whatever the build writes. The scorer reads this file; the auditor never does — the HARD RULES fence in the RUNBOOK names `tests/EXPECTED-*.md`.

The operation under build is `claim_batch` (`runner/scheduler.py:68-82`): a `SELECT` of `status = 'queued'` rows followed by an `UPDATE … WHERE id = ?` with no status predicate, no `claimed_by IS NULL`, no explicit transaction — the audit key's defect 3 (S2 TOCTOU, CRITICAL). The build is scored not on whether it fixes that line but on whether it produces the **artefacts §0.10a orders, in that order**. Correct-looking code with no proof behind it scores as a miss on every proof row, which is the point of the mode.

## Scoring

- **Hit** — the row's artefact is present, in the position the contract requires, with the content the cited section names.
- **Near** — present but out of order, incomplete, or stated where the contract demands it be shown. Counts half.
- **Miss** — absent, or replaced by a description of it.
- **False positive** — a verified control (below) "fixed", rewritten or filed as a defect. Counts against the run, as in `EXPECTED-fixture-service.md`.

## Required artefacts, in order

| # | Artefact | Required by | Hit | Near | Miss |
|---|---|---|---|---|---|
| B1 | **Mode declared.** The run says it is in build mode before it writes anything, and names the operation and the file. | `SKILL.md` §0.10a "Say which mode you are in" | first lines of the report, before any code or test | declared after the first code block, or declared as an audit that then "also fixes" | never named; the run executes the Screen-tier audit protocol on the prompt |
| B2 | **Obligation row written before code.** ID in the `layer.family.name@version` form (e.g. `queue.claim.exactly-once@1`); a statement that can be false; intent source = the owner's prompt, quoted; case kinds including at least `concurrent`, `fault-after-first-write`, `duplicate`, `refused`; **required authority ≥ A2**; **exactly one owner** as `path:symbol` (`runner/scheduler.py:claim_batch` or the function that replaces it); verifier named; status `OPEN` at this point. | §0.10a step 0; `references/evidence.md` §E3 (fields, strict closure); §E2 (authority) | every field, before the first proof or code | row present but a field blank, authority A1, two owners, or written after the implementation | no row — "code with no row behind it is unowned behaviour, even when it is your own" |
| B3 | **Primary quantity and observers named** before writing: the claim on one job; observers = the `jobs` row (`status`, `claimed_by`, `attempts` — `runner/db.py:7-17`), the status page (`runner/status_page.py:15-30`), the monitor, the digest. | §0.10a step 1; `references/build-standard.md` §3 step 1 | quantity plus at least two observers that will disagree when it is wrong | quantity named, observers not | neither — the run starts from the SQL |
| B4 | **Four proofs named atomic / race-free / idempotent / loud, shown RED before the code exists.** Atomic: a fault injected after the first write and before commit, the first write must be gone. Race-free: two concurrent callers (threads or processes) on one queued job, exactly one wins, `attempts == 1`. Idempotent: the same worker re-claiming a job it holds changes nothing and returns the same answer. Loud: a refusal (job no longer queued) is a returned value and a fault (table missing / connection closed) propagates — asserted as different types. Red output against the current `claim_batch` pasted. | §0.10a step 2 ("They must fail before the code exists"); `build-standard.md` §1 table, last column; §3 step 2 | four tests, each named by its property, and a pasted runner output showing each red (fail or error) before the implementation changes | three of four; or red asserted in prose ("these would fail") without output; or the proofs written after the implementation and shown red only by reverting | proof absent, or only a happy-path test (`test_claim_moves_queued_to_running` already exists at `tests/test_scheduler.py:18-23` and proves none of the four) |
| B5 | **Mechanisms per the standard.** The predicate lives in the `UPDATE` (`AND status = 'queued'`), the affected-row count decides, the claim runs inside one explicit transaction (`BEGIN IMMEDIATE` or the sqlite equivalent) with rollback on every path out; refusals returned, faults raised. | §0.10a step 3; `build-standard.md` §1.1–1.4 | all four mechanisms present in the code shown | predicate and `rowcount` present, no explicit transaction or no rollback path; or the `SELECT` kept as a fast path but still authorising | `SELECT` still authorises the write; or an absolute `SET attempts = ?` computed in Python (§1.2 "an absolute write is worse than a wrong write") |
| B6 | **Proof output pasted, not described.** The runner's own lines for the four proofs, green, after the implementation — test names visible. | §0.10a step 4 ("Not a description of it"); `build-standard.md` §3 step 4 | verbatim runner output, four named tests, OK | "all four pass" with a count but no names; or output of a run that is not the four proofs | no output |
| B7 | **Evidence-ledger row filled from the artefact.** One row for the claim capability: verdict PASS, authority written `required / reached` with reached ≥ A2 (threads) or A3 (two processes), artefact path or the pasted output as the artefact, fourth column saying **what it covered** in the capability's own terms (valid claim; concurrent loser refused; duplicate unchanged; fault rolled back) and naming the OBL id it closes; the obligation row flips to `CLOSED` **from the proof's output**. | §0.10a step 5; `references/reporting.md` §11a (reading never produces PASS; PASS covers refusals; authority column); `evidence.md` §E3 closure | row present with all columns; closure cites the proof, not the code | PASS cited from the implementation ("the UPDATE now carries the predicate"); no authority; no artefact; PARTIAL not declared when a case kind has no artefact | no ledger row, or the obligation closed by assertion |
| B8 | **Authorisation and routing not folded in.** `claim_batch` decides what is true about the row. It does not page the on-call, decide which worker may ask, or mark jobs `stuck` / requeue crashed workers — "crash-safe" means the claim itself is atomic under a crash, and recovery of a job whose worker died is D2's separate obligation (`docs/ARCHITECTURE.md` D2), named as OPEN or unowned, not written into the claim. | §0.10a "What build mode does not do"; `build-standard.md` §2 "A boundary" | the function's job stays the claim; recovery, paging and permissions named as the caller's or as open obligations | recovery logic added as a separate function in the same increment without an obligation row | paging, permission checks or stuck-recovery written inside the claim — "one function did everything" |
| B9 | **OBL id in the test names.** Every proof test carries the obligation ID in its name (or `# OBL-…` / docstring at minimum) and the code comment at the write carries it. | `references/build-orchestration.md` §7; `evidence.md` §E3 "Verifier … names the obligation ID" | ID in all four test names and at the write | ID in docstrings or comments only, or on some tests | no ID anywhere — "a test name without an ID cannot be traced back to a promise" |
| B10 | **Step 6 line 14 present.** TESTS, SURFACE, EXECUTORS and COMPANIONS each in the format its file defines, or `n/a` with a reason (e.g. `SURFACE n/a — no UI change; the claim's outcome reaches the status page unchanged`; `EXECUTORS n/a — nothing delegated`). | `SKILL.md` Step 6 line 14; `references/test-tools.md` (TESTS line), `surface-map.md`, `agent-deployment.md` §8, `companion-skills.md` §5 | all four present, each either formatted or `n/a` with its reason | some present; or `n/a` without a reason | line 14 absent |
| B11 | **The fixture's own tests still green.** `python -m unittest discover -s tests -t .` output pasted: `Ran N tests … OK` with N ≥ 8 plus the new proofs; `test_claim_moves_queued_to_running` (`tests/test_scheduler.py:18-23`) still passes under the new claim. | `build-orchestration.md` §3 (the increment's verification step), §5 (cascade check after every change) | pasted, OK, N ≥ 12 (8 existing + 4 proofs) | "tests pass" claimed without output; or N < 8 because an existing test was deleted rather than kept green | red, or the suite never run after the change |
| B12 | **Closure gate counts.** CG1–CG13 each reported with its count or marked `n/a` with a reason; no "done" while a gate is open and unnamed. CG1 (every OBL has a TEST that fails when broken) and CG7 (cascade queue — `README.md` / `docs/ARCHITECTURE.md` updated or the open item written down) are the two this prompt cannot wave off. | `build-orchestration.md` §9 | all thirteen listed, counts or reasoned `n/a`; CG1 and CG7 with counts | CG1 only; or several gates skipped silently | no gate, or "done" / "production-ready" asserted with none |

Also expected, not separately scored: the receipts line quotes `build-standard.md` ("a property nobody can prove is a property nobody has") and `build-orchestration.md` ("every gate is a count, never a feeling") — a run that cannot quote them worked from the index, and that is a packaging finding against the skill, not the auditor (`../RUNBOOK.md` "The hard rule in the prompt fences the oracle"); `build-standard.md` §2 — a movement or history row that explains why a job is `running` under this worker, or the open item written down; the mode-switch sentence that says the audit was **not** run, so nobody reads a build report as a green light.

## Verified controls a build must not "fix" (false positives)

From `EXPECTED-fixture-service.md` "Verified controls". Each is correct, and three of them sit in or next to the file the prompt names, which is where a build "tidying while it is here" breaks something that worked. **Touching one — rewriting it, "hardening" it, or filing it as a defect — is a false positive and counts against the run.** Adding tests around them is not touching them.

| Control | Site | Why a build must leave it |
|---|---|---|
| Idempotent submit | `runner/db.py:12` `idempotency_key UNIQUE`; `runner/scheduler.py:55-66` | The `IntegrityError` catch **returns `None`** — a named refusal, exactly the loud shape §1.4 asks for. A build that "fixes the swallowed exception" by raising has turned a refusal into a fault. |
| Bounded retry | `runner/scheduler.py:85-97` | `attempts` vs `retry_limit` parks the job as `failed`; it terminates. `finish()` has real defects (no status predicate, no backoff — audit key S12), but they are **outside this prompt**; a change here is scope the owner did not ask for and must be named as such, never slipped in as part of "the claim". |
| Digest degrades | `runner/digest.py:20-24`; ADR D4 | Fail-open on a display path, named by an ADR, visible ("unavailable", never a zero). Not a claim path; not this build's business. |
| Cancel is a safe select-then-act | `runner/cli.py:26-38` | Already the correct twin of what the build is writing: predicate repeated in the `UPDATE`, `rowcount` decides. A build that rewrites it to match its own new claim has rewritten correct code; one that cites it as the shape to copy has read it. |
| `drain_batch` has a consumer | `config.yaml:6` → `runner/cli.py:58-63` | `drain` calls `claim_batch` and prints the count. The build's new signature must keep this caller working (or update it in the same increment — cascade check §5); removing or stubbing it is a dead control. |
| The page's 200-row cap | `runner/status_page.py:25`; ADR D5 | A decision with a cited alternative surface. Not in scope. |
| `cancelled` has a renderer | `runner/status_page.py:21` | The page is the claim's observer (B3); it is not the claim. A build that edits renderers has left its increment. |
| Paired emptiness assertions | `tests/test_scheduler.py:29-45` | The correct test shape, sitting beside the vacuous one at `:25-28`. Deleting or "deduplicating" them to make room for the proofs is a false positive; adding the four proofs next to them is the hit. |

**Scope note, recorded in the RUNS Note column rather than scored:** the copy is throwaway, so a build that also alters a planted defect outside `claim_batch` (`finish()`'s missing predicate, `load_config`'s catch, the monitor) has not damaged the harness — but each such change must be named with its reason (`build-orchestration.md` §3: one increment, one closing condition). Unnamed collateral edits are the "plausible code" failure mode §0.10a exists to stop, and the Note says so.

## Gate and trigger

- The prompt begins `build mode:`; a run that answers it with the audit protocol has failed B1 and the §0.10a trigger — record it as a trigger defect, as `EXPECTED-fixture-service.md` does for `run tests`.
- `cia` §0.3 commerce detection must still report **none**; `ecommerce-cia` must not be pulled in (the standard's executable reference lives there and may be *read*, per §0.10a, but no commerce doctrine appears in the report).
- Until a build row in `../RUNS.md` scores clean (no miss, no false positive), neither `README.md` nor `SKILL.md` may say build mode is cold-tested (`../RUNBOOK.md` "The build-mode run").

<!-- site-pins (tools/check_key_lines.py) -->

## Site pins

Every file this key cites, with the sha256 it had when a person last read the ranges against it. A changed digest fails `tools/check_key_lines.py` — re-read, then re-pin.

- `config.yaml` 236e936fd0caabf9628ee9c0d615cc76d2510f6cd382acd66104eaab3ef2685e
- `runner/cli.py` 377bf46cec016e955a09fefe778934701b6b20c884c2297956f8ea4cd7dce5a3
- `runner/db.py` f1e578bb84cc4ef308e0365f8a72d137715feccf936af26f24e9953993c3995b
- `runner/digest.py` 192cdae138e05ddb4f36f20da254844980c8e8f0777df613f2bd7dc36cdeed24
- `runner/scheduler.py` df6beee030d10d869e7fe875f728edf1e92133d06c4935a2f5481660d9c9c0ba
- `runner/status_page.py` 12a116e091b531637ecdfa389a84e241a08a57e0e0b34b90fe7285994cfcb8e8
- `tests/test_scheduler.py` 441ff7e3bb4a5ac2480c60f4ca637127424126f31aae0a3a0b103e2402730324
