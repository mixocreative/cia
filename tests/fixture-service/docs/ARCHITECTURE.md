# fixture-service architecture

## D1 — Outbound calls retry with backoff

Every job handler wraps its outbound HTTP call in `runner.legacy_retry.with_backoff` so a flapping downstream does not fail the job on the first refusal.

## D2 — Stuck jobs are an operator decision

A job running longer than `stuck_after_minutes` is marked `stuck`, shown on the status page with a **Requeue** and a **Fail** action, and the on-call is paged when `alerts_enabled` is true. The monitor never requeues by itself.

## D3 — One job per idempotency key

A client that retries a submit must not create a second job. Enforced by the unique index on `jobs.idempotency_key`.
