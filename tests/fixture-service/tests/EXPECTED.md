# fixture-service — answer key

Ten planted defects and two verified controls. A Screen-tier `/cia` run on this directory must report every row below, with the sweep, a `path:line` inside the cited range, and a grade no lower than shown. Extra findings are scored separately (see `../RUNBOOK.md`); a planted row the run did not report is a **miss** and blocks the skill change that caused it.

Run the suite first (`python -m unittest discover -s tests -t .`): 4 tests, all green. Every defect below sits under that green.

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
| 10 | **S21** runner contamination | `tests/test_scheduler.py:30-33` | `test_config_from_real_file` writes `os.environ["FIXTURE_ALERTS"]` and never restores it; every test after it in the process sees it. | Snapshot the environment before, restore after; clear on the way in | MEDIUM |

Also expected, not separately scored: **S12** — `finish()` (`runner/scheduler.py:65-77`) re-queues on failure with no backoff and no per-step timeout, and since defect 8 nothing backs off; **S14** — the run states its scope as this directory and lists the modules on the map.

## Verified controls (must appear under Verified Controls, not as findings)

| Control | Site | Why it is correct |
|---|---|---|
| Idempotent submit | `runner/db.py:12` `idempotency_key UNIQUE`; `runner/scheduler.py:35-45` | A repeat submit hits the unique index, the `IntegrityError` is caught **and returned as `None`** — a distinct, tested outcome (`test_enqueue_is_idempotent`), not a swallowed error. D3 satisfied. |
| Bounded retry | `runner/scheduler.py:65-77` | `attempts` is compared to `retry_limit` and the job parks as `failed` with a Retry button on the status page; the loop terminates. |

## Gate and trigger

- `ecommerce-cia` §0.3a gate must **FAIL** (no gateway code, no orders/cart schema, no checkout route, no commerce dependency). If a paired or automatic run pulls in commerce doctrine here, that is a routing defect.
- `cia` §0.3 commerce detection must report **none**.
- A bare `run tests` in this directory must run `python -m unittest discover -s tests -t .` first, report `Ran 4 tests … OK` with the count, and only then offer the Screen-tier audit in one line. Starting the protocol on that request is a trigger defect (§0.3).
