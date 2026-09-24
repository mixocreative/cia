# fixture-service architecture

## D1 — Outbound calls retry with backoff

Every job handler wraps its outbound HTTP call in `runner.legacy_retry.with_backoff` so a flapping downstream does not fail the job on the first refusal.

## D2 — Stuck jobs are an operator decision

A job running longer than `stuck_after_minutes` is marked `stuck`, shown on the status page with a **Requeue** and a **Fail** action, and the on-call is paged when `alerts_enabled` is true. The monitor never requeues by itself.

## D4 — The digest degrades, it does not fail

`runner.digest` is a convenience for a human reading a summary. It is not a control, nothing acts
on its output, and no operation is recorded as handled because it rendered. So it catches its own
storage errors and says the number is unavailable — a *visible* degradation, never a zero, because
a zero is indistinguishable from a quiet week. This is the one place in this service where a
fail-open posture is the intended choice, and it is the choice because the path is display-only.

## D5 — The status page is a triage window, not a report

The page shows the most recent 200 jobs and deliberately offers no paging: an operator opens it to
see what is wrong *now*. Totals over all history are `runner.digest`'s job, and the operator CLI
reaches any single job by id. A paging control here would invite using the page as a report, which
is the thing the digest exists to serve.

## D3 — One job per idempotency key

A client that retries a submit must not create a second job. Enforced by the unique index on `jobs.idempotency_key`.
