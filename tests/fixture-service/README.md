# fixture-service — a planted-defect job runner for testing `cia`

A deliberately small Python service (stdlib only, no framework) that passes its own test file
and contains nine planted defects, one per sweep the skill claims to catch, plus two controls
that are correct and must be reported as verified, not flagged.

It is **not** a commerce system. That is part of the test: `ecommerce-cia`'s §0.3a gate must
FAIL here, `cia`'s §0.3 commerce detection must report *none*, and a bare `run tests` must run
`python -m unittest` first and only then offer the Screen-tier audit.

**Do not fix anything in this directory.** The answer key is `tests/EXPECTED.md`; the procedure
is `../RUNBOOK.md`.

Layout:

```
config.yaml                  runtime configuration (one key is never read)
runner/db.py                 sqlite schema + connection
runner/scheduler.py          claim queued jobs and run them
runner/monitor.py            health check over workers and stuck jobs
runner/status_page.py        operator status page, one renderer per job state
runner/legacy_retry.py       old retry helper
tests/test_scheduler.py      the service's only tests
docs/ARCHITECTURE.md         the one design decision the audit must respect
```
