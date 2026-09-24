# fixture-service — answer key

**Twelve** defects (eleven planted, one the harness acquired by accident) and **eight** verified controls. A Screen-tier `/cia` run on this directory must report every row below, with the sweep, a `path:line` inside the cited range, and a grade no lower than shown. Extra findings are scored separately (see `../RUNBOOK.md`); a planted row the run did not report is a **miss** and blocks the skill change that caused it.

Run the suite first (`python -m unittest discover -s tests -t .`): 8 tests, all green. Every defect below sits under that green.

## Planted defects

| # | Sweep | Site | Defect | Invariant broken | Min grade |
|---|---|---|---|---|---|
| 1 | **S5** dead control | `config.yaml:3` `alerts_enabled`; `runner/monitor.py:18-37` | `alerts_enabled` is loaded into `cfg` and read by nothing (grep → config + `DEFAULTS` only). The monitor prints to stderr; nobody is paged. `docs/ARCHITECTURE.md` D2 promises paging. | Every control has a consumer; a design-document promise with no channel is S13 too | HIGH |
| 2 | **S3** fail-open (configuration axis) | `runner/scheduler.py:11-29` | `load_config` catches `Exception` and returns `DEFAULTS`. A mistyped path, a bad permission or a malformed file runs the service on defaults with no error anywhere. | Configuration reads fail closed unless an ADR names the choice | HIGH |
| 3 | **S2** TOCTOU | `runner/scheduler.py:48-63` | `claim_batch` SELECTs `status = 'queued'` then UPDATEs `WHERE id = ?` with no status predicate and no `claimed_by IS NULL`. Two workers claim the same job; both run it; `attempts` counts twice. | Carry the precondition in the `WHERE`; read the affected-row count | CRITICAL |
| 4 | **S20** blind instrument | `runner/monitor.py:22-28, 37` | An unparseable `last_seen` is counted in `unknown`, never reported; `monitor: 0 problems` and exit 0 are printed whether every worker was checked or none could be. | A detector reports coverage separately from findings; blind ≠ clean | HIGH |
| 5 | **S20** dead watchdog | `runner/scheduler.py:79-86`; `config.yaml:5` | Worker heartbeats are written to `workers` and to `heartbeat_path`; the monitor reads the table but nothing reads the file, and nothing outside the service checks that the monitor itself ran. No outermost check. | Something reads every heartbeat; name the outermost check or say NONE | HIGH |
| 6 | **S22** unrendered state | `runner/status_page.py:15-20, 26-30`; `runner/db.py:10` names `stuck` | No renderer for `stuck`; the loop `continue`s, so a stuck job vanishes from the operator's page. Empty state renders a blank row with no text. | Every reachable state has a surface; an empty state says something | HIGH |
| 7 | **S16** terminal-state accountability | `runner/monitor.py:33-35`; `runner/scheduler.py` (no writer of `status = 'stuck'`) | A job running past `stuck_after_minutes` is printed to stderr once per monitor run and never transitions; there is no queue, no action, and D2's Requeue / Fail actions do not exist. | Every non-terminal state has an advancer or a desk | HIGH |
| 8 | **S13** orphan capability | `runner/legacy_retry.py`; `docs/ARCHITECTURE.md` D1 | `with_backoff` has no caller (grep → definition only). D1 says every handler uses it. Designed, documented, unbuilt. | A capability named by a design document exists or has a gap-register row | MEDIUM |
| 9 | **S21** vacuous pass | `tests/test_scheduler.py:25-28` | `test_no_jobs_are_stuck_on_a_fresh_db` asserts `stuck_jobs(...) == []` on a job that just started; no test anywhere proves `stuck_jobs` can return a row. | A test asserting emptiness needs a sibling proving non-emptiness | HIGH |
| 12 | **S3** fail-open at a log level nobody reads | `runner/scheduler.py:33-49` (`load_worker_identity`), called from `runner/cli.py:60` | The worker identity file is read inside a `try`; on `OSError`/`ValueError`/`KeyError` it writes **`log.debug`** and returns the default name `"worker"`. Production runs at INFO, so the line is never seen, and every worker that falls back is stamped into `claimed_by` under the same name — two workers become indistinguishable in the jobs table and on the status page. | A failure reported below the level production runs at is not reported | HIGH |
| 11 | **S13** orphan wiring | `runner/cli.py:46`; `config.yaml` (no `db_path`) | `connect(cfg.get("db_path", ":memory:"))` reads a key the config never sets, so **every** `python -m runner.cli` invocation opens a fresh in-memory database and discards it on exit: the operator CLI is wired to nothing. | A control an operator reaches must reach the real state | HIGH |
| 10 | **S21** runner contamination | `tests/test_scheduler.py:30-33` | `test_config_from_real_file` writes `os.environ["FIXTURE_ALERTS"]` and never restores it; every test after it in the process sees it. | Snapshot the environment before, restore after; clear on the way in | MEDIUM |

Also expected, not separately scored: **S12** — `finish()` (`runner/scheduler.py:65-77`) re-queues on failure with no backoff and no per-step timeout, and since defect 8 nothing backs off; **S14** — the run states its scope as this directory and lists the modules on the map.

### A note on row 12's provenance

Row 12 was planted **on purpose, on 2026-09-24, because the corpus found the gap and the fixtures
could not have.** Every failure planted here before it was *silent*; not one logged at the wrong
level, so no run was ever asked to notice that a `catch` which logs at DEBUG is silence in
production. A real fix commit in another repository (`WilliamAGH/findmybook`, *"stop swallowing
exceptions in startup config normalization"*) was the corpus's first MISS for exactly that
reason, and a doctrine lesson with no fixture row behind it is a lesson that rots. This one now
has both: S3 in `references/sweeps.md` grades the level, and this row fails any run that does
not.

### A note on row 11's provenance

Row 11 was **not planted**. It arrived with the precision controls on 2026-09-24 — I wired the new operator CLI to a config key I never added — and the cold Sonnet run found it the same day, live, by enqueuing in one process and running `cli digest` in another. It is kept for the reason `fixture-shop-live`'s L7 is kept: a defect the harness acquired by accident and a run caught by *running* is better evidence for the doctrine than one written to be found. It also makes control C4 sharper rather than weaker — `cli.cancel`'s compare-and-swap is still correct, and an auditor must now separate a correct mechanism from a mechanism wired to the wrong store.

## Verified controls (must appear under Verified Controls, not as findings)

Eight of them, and six were added 2026-09-24 **to measure precision**. Each is written to look
like one of the planted defects and is correct. An auditor that flags everything scores well on
recall and badly here, which is how an audit tool actually dies — not by missing a bug, but by
being ignored after two noisy reports. **A control filed as a finding is a false positive and
counts against the run.**

| Control | Site | Looks like | Why it is correct |
|---|---|---|---|
| Idempotent submit | `runner/db.py:12` `idempotency_key UNIQUE`; `runner/scheduler.py:35-45` | a swallowed exception | The `IntegrityError` is caught **and returned as `None`** — a distinct, tested outcome (`test_enqueue_is_idempotent`), not a swallow. D3 satisfied. |
| Bounded retry | `runner/scheduler.py:65-77` | an unbounded requeue loop | `attempts` is compared to `retry_limit` and the job parks as `failed`; the loop terminates. |
| **Digest degrades** | `runner/digest.py:20-24` | **defect 2** — a catch that returns a default | Fail-open on a **display** path, which is the axis S3 itself exempts, named by **ADR D4** with its reason, and the degradation is *visible* — it says "unavailable", never a zero. Nothing acts on its output. |
| **Cancel is a safe select-then-act** | `runner/cli.py:26-38` | **defect 3** — read a status, then write | The predicate is **repeated in the `UPDATE`** and `rowcount` decides the answer, so a worker that claims the job in between wins and the operator is told no. This is the correct twin of `claim_batch`; an auditor that flags both has not read the `WHERE`. |
| **`drain_batch` has a consumer** | `config.yaml:6` → `runner/cli.py:60` | **defect 1** — a dead control | A bare-identifier grep hits config and exactly one runtime reader. README documents the command. S13's own false-orphan rule covers this: grep the identifier alone, and read every hit. |
| **The page's 200-row cap** | `runner/status_page.py:25`, ADR D5 | an unpaged list (S22.7) | D5 names it a triage window and names where totals live instead (`runner.digest`), and single-job access is the CLI. A cap with a cited alternative surface is a decision, not a gap. |
| **`cancelled` has a renderer** | `runner/status_page.py:21` | — | The counter-example to defect 6: five of six statuses render, which is what makes `stuck`'s absence a defect rather than an unfinished module. Flagging this one means the auditor listed the enum instead of diffing it. |
| **Paired emptiness assertions** | `tests/test_scheduler.py:29-45` | **defect 9** — a test asserting nothing happens | `test_cancel_returns_false_once_a_worker_holds_the_job` is immediately followed by the sibling proving the true case, and `test_digest_says_so_when_there_is_nothing` by one proving the non-empty case. This is the shape defect 9 is missing, sitting next to it. |

## Gate and trigger

- `ecommerce-cia` §0.3a gate must **FAIL** (no gateway code, no orders/cart schema, no checkout route, no commerce dependency). If a paired or automatic run pulls in commerce doctrine here, that is a routing defect.
- `cia` §0.3 commerce detection must report **none**.
- A bare `run tests` in this directory must run `python -m unittest discover -s tests -t .` first, report `Ran 8 tests … OK` with the count, and only then offer the Screen-tier audit in one line. Starting the protocol on that request is a trigger defect (§0.3).
