# The reference-guided wiring walk — function, wiring and lifecycle rules, proved together

Loaded in Step 2 right after the step-0 map in `sweeps.md` and before the sweeps run. It turns the map into the
audit's deliverable: a lifecycle state map, seven answers per connection, a deliberate fault set, and a rule
traceability matrix with a gap register. It is the **default answer when the owner asks "what should we audit
next?"** on any system built in-house: a **reference-guided Walk** — map every primary flow, inspect every
connection, run the targeted failures, and hand back a gap register with exact code locations and proof status.

Commerce has its own, stricter version (`ecommerce-cia`'s `wiring-walk.md`: checkout, payment, refund,
shipping, invoice, download). This file is the same method for everything else — job runners, sync and import
pipelines, APIs, CLIs, desktop apps, Blender add-ons, n8n flows, AI agents.

---

## §1 — The question this file exists to ask

A feature comparison asks: *"Do we have retries?"* — *"Do we have import?"* — *"Do we have undo?"*

A wiring audit asks a sentence of this shape, written **for this system**: *"What happens if the work is
accepted, the confirmation from the other side is lost, the data underneath changes, the follow-up write fails,
and the operator looks at it two days later?"* For a job runner: *the job is claimed, the worker dies, the input
file is replaced, the result write fails, and someone opens the dashboard on Monday.* For an import: *the batch
is half applied, the source is re-sent, a row changed upstream, the index update fails, and a user searches for
it tomorrow.*

**That sentence is where in-house systems break**, and no feature list can answer it. Every run writes it for the
audited system **in the report's first paragraph** and answers it with evidence: what the user saw, what the
operator's screen showed, what the store held, which job noticed, and when.

## §2 — A reference is a checklist of stages, never the truth

Where a mature system does the same job — a queue library's documented job states, a sync tool's documented
conflict rules, a framework's request lifecycle, the platform's own add-on lifecycle, a protocol's RFC — use it
to list **which stages a normal implementation has**, so a stage this one skipped is noticed. It does not say
what is correct here.

- Pin the version you compared against; read its open issues — a reference with known defects in the very stage
  you are comparing is a weaker checklist, and its docs may be ahead of or behind its code.
- **Compare workflow shape, then judge against stricter rules:** the project's own invariants (`doctrine.md`
  §8.0), owner decisions and ADRs, the **official contracts** of every external party (API docs, file formats,
  protocols), and the architecture. Reference vs authority disagreement is a contradiction row
  (`evidence.md` §E7), never a finding against the project.
- A reference stage the project deliberately lacks is `NOT-APPLICABLE` with the scope evidence.
- No reference exists? The expected path comes from the spec, the ADRs and the owner's own words — say so in the
  column header.

## §3 — Three layers, all three every time

| Layer | The question | Typical proof | A finding here sounds like |
|---|---|---|---|
| **L1 Function logic** | Does each function calculate, validate, authorise and change state correctly **on its own**? | unit test with boundary values | "the retry delay overflows after the 31st attempt" |
| **L2 Relationship wiring** | Does every function that must call another **actually call it**, pass the right values, **persist** the result, and handle retry, error and **partial completion**? | integration test that breaks the connection (§5 Q7) | "a failed result write leaves the job `running` and nothing re-queues it" |
| **L3 Lifecycle rules** | Does the **combined system** obey its rules when events arrive **late, twice or out of order**? | fault injection (§6) through the real entry points, read at every observer | "a late completion from a timed-out worker overwrites the retry's result" |

The audit never stops at L1. **Every finding names its layer**; the report counts findings per layer, and a report
with L1 findings only has not been run.

## §4 — The lifecycle state map (mandatory, one row per lifecycle)

Take the lifecycles from the step-0 map: every System 1 unit of work that has a start, intermediate states and an
end. Typical rows — keep the ones the system has, add its own:

| Lifecycle | Reference / expected path | Our path | Failure / retry path | Operator-visible result |
|---|---|---|---|---|
| **Intake** (submit, enqueue, import, request) | accept → validate → store | the real route, form or command, `path:line` | duplicate submit; malformed input; accepted then dropped | a clear refusal, or a record in a named state |
| **Processing** (claim, run, transform, render) | claim → work → result | the worker / handler chain | worker dies mid-way; two workers claim; result write fails | a stuck item flagged, or recovery |
| **External call** (API, webhook, model, file system) | request → response → apply | the client, its timeout and its retry | timeout with remote success; duplicate or late reply; rate limit | the disagreement visible, or reconciled |
| **Reversal** (cancel, undo, delete, rollback, refund-like) | request → reverse → confirm | the reverse path | partial reverse; reverse twice; reverse after completion | a reversal exception, visible |
| **Output / notification** (email, report, export, push) | event → message → delivered | the sender and its queue | send fails; sent twice; recipient gone | a delivery problem on a screen |
| **Retention / access** (stored artefact, link, cache, permission) | store → reference → retrieve | the storage key and who reads it | artefact removed or replaced; link expired; cache stale | recoverable access, or a visible broken reference |

Every cell names real states, functions, tables and screens — `path:line` where it is code — or `UNVERIFIED`. The
**Our path** column comes from the code and the running system (`browser-walks.md` §12 ladder), never from docs.
The **Operator-visible result** column is checked on the screen the operator already opens (SKILL §0.11 item 6); a
log line, an exit code or a table nobody renders counts as invisible.

## §5 — Seven questions for every connection

List every connection on the map (System 1 → System 1, System 3 → System 1, System 4 ingress and egress,
worker → screen). Each gets one row and **seven answers**, each with evidence or `UNVERIFIED`:

| # | Question | What "yes" needs | Sweep |
|---|---|---|---|
| Q1 | **Does the caller actually invoke the service?** On every path, including the error path and the admin path? | the call site, read; a runtime trace showing it fire | S5, S13 |
| Q2 | **Is the result persisted?** Before anything that depends on it, in the same transaction where it must be? | the write and a read-back | S16, §0.12 |
| Q3 | **Is the operation safe if retried twice?** | an idempotency key or a state predicate in the write; a test that sends it twice | S2, S12, S23 |
| Q4 | **Is there one authoritative state when the systems disagree?** | a written authority rule and the code that applies it (re-read, reconcile) | S1, S4, S18 |
| Q5 | **Can a job stop without anybody noticing?** | a liveness check whose silence is itself an alert | S16, S20 |
| Q6 | **Does an unresolved case appear on an operator screen**, rather than only in logs? | the badge / flag / filter, rendered | S22, §0.11 |
| Q7 | **Is there a test that breaks this exact connection**, rather than testing each side alone? | a test that makes the callee fail, time out or answer twice, and asserts the caller's outcome | S21, S24 |

A connection with a `no` or `UNVERIFIED` on any of Q1–Q7 is a gap-register row (§9). Ten classes each tested alone
prove ten functions, not nine connections.

## §6 — Deliberate fault injection: recovery, or a visible operator problem

Run each applicable fault through the real entry point against a local or test instance (`browser-walks.md`
§12–§13; never production, never a live third party with side effects). The **only two acceptable outcomes**:
**(a) the system recovers by itself** to a consistent state at every observer, or **(b) the problem becomes
visible on the operator's screen** with enough said to act on. A silent wrong state, a log line or a stuck item
with no flag is a finding, graded HIGH or above on the primary path.

| # | Fault | Typical injection | What to read afterwards |
|---|---|---|---|
| G1 | **Reject a downstream write mid-flow** | make the result / follow-up write fail after the first step committed | the item's state, any retry, the operator flag |
| G2 | **Replay a message or request** | send the same job, webhook, import batch or API call twice, and again later | exactly one effect at every observer |
| G3 | **Deliver an event before its predecessor** | completion before start, update before create, reply before the request is recorded | every observer agrees afterwards, in every order |
| G4 | **Two actors on the last unit of a scarce resource** | two workers claim one job, two users take the last seat / slot / quota, across processes | exactly one wins, the other is refused clearly |
| G5 | **A dependency times out while the far side succeeded** | local timeout, remote completion (and the reverse) | the disagreement is reconciled or flagged, never doubled |
| G6 | **Remove an artefact a finished record points to** | delete or replace the file, blob, row or model the record references | recoverable access, or a visible broken reference |
| G7 | **Stop a scheduled or background job** | disable or kill the worker / cron / watcher longer than its period | someone is told (S20); pending items surface instead of ageing silently |

A fault with no site on the map is `N/A` with the map row that proves it; one the environment cannot exercise is
`UNPROVEN` with the missing condition — never "skipped".

## §7 — The question banks: ask them, then answer them in the report

Per lifecycle, each answer citing its evidence or `UNVERIFIED`; the project's own rules are added to them.

**Intake** — Does what the user saw (preview, estimate, validation message) equal what the server computed and
stored? Does the stored record **preserve the facts that held at the time** (inputs, versions, settings, consent),
so a later edit cannot rewrite history? Does one accepted request lead to **exactly one** unit of work?

**Processing** — Does every accepted item reach a terminal state, or a visible queue? Can two workers ever hold the
same item? If a step after the first commit fails, is the item recoverable and flagged?

**External call** — Is external input validated **before** it is trusted (S11)? When local state and the far side
disagree, which wins (Q4), and is the disagreement recorded? Is the retry bounded, and only on idempotent actions?

**Reversal** — Is the reversal **limited to what was actually done** (never more than was applied)? Does a
**partial** reversal leave every dependent record correct? Do all the side effects — data, files, notifications,
derived records, the operator screen — agree afterwards? If the reverse runs twice or the reply is late, does the
system settle once and show the unresolved case?

**Output / notification** — Is each message sent once per event, and is a failed send visible and retryable?

**Retention / access** — Does a record pin the version of the artefact it refers to? Can a user whose link expired
recover without someone editing the database?

## §8 — The rule traceability matrix (the deliverable)

The report's centrepiece is this matrix — one row per rule, not a code review. Seed rows every in-house system
carries (rephrase to the system; drop a row only with a map row proving it has no site):

| Rule | Code that enforces it | Connected systems | Proof | Outcome |
|---|---|---|---|---|
| A unit of work is processed once, never twice | claim / dedupe + state predicate | intake, queue, worker, store | concurrency + replay tests (G2, G4) | covered / gap |
| External input is never acted on unverified | validation / signature / schema at ingress | caller, handler, store, side effects | malformed + forged + early tests (G3) | covered / gap |
| Every accepted item reaches a terminal state or a visible queue | state machine + sweeper | worker, scheduler, operator screen | forced-failure walk (G1, G7) | covered / gap |
| Every unresolved state reaches an operator | reconciliation + flag UI | worker, dashboard / admin list | forced-failure walk (G5, G7) | covered / gap |
| A reversal never exceeds what was done | reverse path + bounds | store, files, notifications | boundary + partial + double tests | covered / gap |
| A delivered artefact stays retrievable | pinned reference + storage | store, files, links | artefact-removed walk (G6) | covered / gap |

"Code" is `path:symbol`; "Proof" is a test or artefact from **this run** at the right authority (`evidence.md`
§E2) — a unit test cannot cover a rule that spans systems; "Outcome" is `covered` only when that proof ran and
passed this run. Each row is also an obligation (`evidence.md` §E3).

## §9 — The gap register

Every `gap`, every connection with a `no` on Q1–Q7, and every fault whose outcome was neither (a) nor (b):

| Gap ID | Layer (L1/L2/L3) | Lifecycle | Rule / connection | Exact location (`path:line`) | What breaks, in one sentence | Proof status | Severity | Fix owner |
|---|---|---|---|---|---|---|---|---|

**Proof status:** `PROVEN` (this run reproduced it — cite the artefact), `READ` (found by reading; no run yet),
`UNPROVEN` (attempted, the environment would not answer), `UNVERIFIED` (not attempted at this tier). A register
where every row is `READ` is a code review and says so in its first line.

## §10 — Tiers, and the next audit to run

- **Screen:** §4 map for every lifecycle; §5 for every connection on the primary flow; G2 and G4; the §8 seed rows.
  Everything else `UNVERIFIED`.
- **Walk (the recommended next audit):** §4 and §5 in full; every applicable fault G1–G7; every §7 question
  answered; the §8 matrix for every primary-path rule; the §9 register with exact locations and proof status.
- **Full:** as Walk, plus every rule variant and terminal/recovery path, and a deliberate mutation of each
  `covered` row's proof to show the test can fail (S21).

## Report lines (Step 6)

```
Wiring walk (wiring-walk.md): wiring question stated for this system: yes | no · lifecycles mapped L (reference: <system@version> | spec only) · connections C, gaps on Q1–Q7: G · faults G1–G7: N run / A applicable — recovered R, visible to operator V, silent S · findings by layer L1/L2/L3: a/b/c · rule rows T: covered X / gap Y / unverified Z · gap register: path
```

---

**Reading receipt: _ten tested classes are not nine tested connections_.** Quote this phrase on the report's
receipts line (Step 6) to show this file was read rather than inferred from the skill's index. It appears nowhere
else.
