# Sweeps S1–S5 — state and boundaries: snapshots, TOCTOU, fail-open, semantics, dead controls

> Part of `references/sweeps/` (index: `README.md`). Split from the former `sweeps.md` on 2026-11-09 - text unchanged. Read every file in the folder per §0.9.

## S1 — Snapshot-vs-live reread (temporal coupling / stale snapshot)

For every value persisted at one moment (deadline, quota, reservation, computed price, cached permission, offered options), enumerate every later reader of the same concept and classify it as "reads the snapshot" or "re-reads live config". A later reader that re-reads live while an earlier writer froze a snapshot is a finding: the two disagree after any config change.

**S1.1 — the same setting read twice inside one operation (2026-09-24, found in a live checkout).**
S1's usual shape is a writer that froze a snapshot and a later reader that re-reads. The sharper
instance is *inside a single transaction*: one operation reads a setting, uses it for the figure it
quotes outward, and then **reads it again** for the figure it records. A checkout read its
international surcharge rate twice — once to compute the amount the payment gateway would be asked
for, once for the rate written on the order row — so a settings table that changed, or failed,
between the two produced an order **whose recorded rate did not explain the amount charged**.
Nothing throws. The discrepancy surfaces weeks later at reconciliation, as an order nobody can
account for, and by then the settings have been read a thousand times since.

Read the operation as a unit: **every external value it depends on is read once, at the top, and
carried.** Two reads of one name inside one operation is the finding, whether or not you can
construct the interleaving — the argument "the window is tiny" is an argument about likelihood, and
the cost here is an unexplainable row of the primary quantity (here, money), which is the expensive kind of rare. The same shape outside commerce: an exporter that reads the unit scale once for the geometry it writes and again for the header it records, so a file whose header does not explain its own coordinates. The same rule
covers a clock (`now()` twice in one operation gives two times), a random source, a feature flag,
and anything whose second read can disagree with its first.

## S2 — Select-then-act predicate loss (TOCTOU race)

For every worker or batch that SELECTs candidates and mutates them one by one, the per-row UPDATE/DELETE must re-state the full selection predicate, not only the status column. A predicate checked at SELECT and dropped at UPDATE is a time-of-check/time-of-use finding.
**S2.1 — the identity a limit counts (2026-09-15).** A per-address limit that does not normalise
the address counts `me@x`, `Me@x` and `me+1@x` as three people; a bot rotates the alias per try.
Lower-case and strip the `+alias` before counting (keep the original for delivery). A per-IP
limit behind a proxy counts every visitor as one — read the proxy's client header from a
*trusted* proxy only, and note which throttles share the assumption. A per-product limit
("two per customer" on a drop) that lives in the form is no limit at all; it is a `WHERE` in
the placement, and it needs the identity it counts written down: account, verified phone, or
card fingerprint.

**Grading.** The dropped predicate is graded by what the race does to the unit of work, not by the
size of the fix. Two workers executing one job, one writer overwriting another's terminal state, a
paid record marked expired — the primary unit duplicated or lost **with nothing that detects it** —
is **CRITICAL** (undetectable state divergence, `reporting.md` §10); the same race where a later
check or a person would notice is **HIGH**. Three fixture runs graded this HIGH by reflex; the
question to ask is "who finds out", and if the answer is nobody, it is CRITICAL.


**The runtime twin — fire it twice (2026-09-24).** This sweep produces a *prediction*, and the
report then grades the prediction. When the system is running — and §0.6 requires it to be at
every tier — that prediction is one minute away from being an observation: fire the same
operation twice concurrently against a row prepared so exactly one may win, then read the row
(`browser-walks.md` §13). Both succeeded → the finding is CONFIRMED and the two responses are
its artefact. One refused → something holds between the read and the write; name it in the
verified controls and downgrade honestly. One won and the loser vanished with no error, no
message and no row → a second finding, S22's, usually worse than this one. A race graded from
reading alone, on a system that was up on this machine at the time, is evidence left on the
floor — and its confidence is HIGH-CONFIDENCE, never CONFIRMED.

## S3 — Catch-block failure posture (fail-open default)

For every `catch` on a critical path, write one line: what is caught, what happens next, fail-open or fail-closed. Fail-open on a configuration, permission, or feature-flag read is a finding unless an owner decision or ADR names that exact choice and its reason. **A secret derived from the environment's identity is a time bomb.** Any salt, key or token with a computed fallback — `hash(hostname)`, `hash(__DIR__)`, the container id, an ephemeral machine name — silently changes when the environment is rebuilt, and everything hashed against it stops verifying with no error anywhere. Check three things for each: production fails closed when it is unset rather than computing one; the value survives a container recreation; and every process that reads it (web, CLI tool, worker, test) computes the *same* one. A password written by a host-side CLI that cannot verify inside the container is this defect, and it reads as "wrong password" forever. Fail-open is not one posture: name the axis. On a **display or read path** (a listing, a search, a recommendation) fail-open to an empty or degraded result may be the right System 5 policy, provided the degradation is visible on a screen (S22) and counted by a detector (S20). On a **primary path (money, the user's saved work, job results, committed data), entitlement, permission, or configuration path** fail-open is a finding unless an owner decision or ADR names that exact choice and its reason. Grade the two axes separately, and say which one each `catch` sits on.

**Grading.** A `catch` on the primary path that answers success — returns `true`, returns the
defaults, sends 200, stays silent — while the guarded operation did not complete is **CRITICAL**
when the caller acts on that answer and nothing else will notice (the caller stops retrying, the
record is now wrong): a verify that returns `true` on its own exception, a catch-all around a
write that only ever meant to absorb the duplicate-key case. The same fail-open on a
configuration or flag read, where the wrong value is at least visible in behaviour, is **HIGH**.
File it here, under S3, even when the input that triggered the catch was malformed (that is S11's
cause; the posture is S3's finding).

**The log level is part of the posture (2026-09-24, from a corpus miss).** A `catch` that logs is
not thereby reporting. Production runs at INFO or WARN, so **a failure logged at DEBUG or TRACE is
silence with a receipt** — the line exists, the operator's log does not contain it, and the code
reads as handled to anyone grepping for `log.` on the failure path. The shape to hunt, verbatim
from the commit that fixed it:

```java
} catch (IOException | SecurityException e) {
    // Silently continue if .env loading fails, but log at debug level
    log.debug("Skipping .env file loading: {}", e.getMessage());
}
```

The application then boots on defaults, and its own comment says so. The maintainer's fix threw.
This sweep's first corpus miss was exactly this site: a cold run audited that file, filed a
different fail-open in it, and walked past this one because it logged.

So for every `catch` on a primary path, write the level next to the posture: **`debug`/`trace` is
fail-open-and-silent, and it is graded as though there were no log line at all**: the grade the
Grading paragraph above gives the silent case, so a fallback on a configuration read is HIGH, never
MEDIUM. Any file or setting the process reads at startup to decide how it behaves or what it calls
itself is a configuration read, whatever the file is named. A fallback listed in a sweep line and
not filed is the miss this paragraph exists to stop. `info` is
fail-open-and-buried unless something reads it (S20 — a line in a stream nobody watches is the
detector problem one storey down). `warn`/`error` reporting to a channel a person reads is the
minimum for "reported", and a screen is the minimum for "handled" (S22). The comment beside the
catch is evidence of intent, not of reporting: *"silently continue"* written by the author is the
author agreeing with the finding.

## S4 — External field semantics from the source document (semantic drift)

For every third-party field the code branches on (API status, webhook type, protocol sub-code), cite the vendor spec page or RFC section that defines it. A mapper comment is not evidence. If the spec distinguishes a family field from a subtype field, confirm the parser reads the one present in every case. No spec read → report line says "field semantics unverified". **Sample code is not a specification.** A vendor's runnable example proves the envelope it exercises and nothing else — it names no response fields, no status codes, no retry or acknowledgement rule. When the only vendor source on disk is a sample pack, the report says so and lists the manual that is missing; if the vendor publishes it, fetch it before writing a line against the boundary. A handoff note claiming "the sample folder is the complete authority" is an S4 finding, not a fact. **Gates must exist for every family that reaches them.** For every predicate a reducer, state machine or settlement path branches on (a status field, a close flag, a sub-code), list every input family that can arrive at that line and confirm the field is defined for each of them in the vendor document.
A gate on a field that exists for one family only (a card-only close status read for a bank-transfer or pickup result) leaves the other families stuck in their prior state forever, with no error, no expiry and no alarm — the quietest state defect there is, and in a payment flow the quietest money defect. **The vendor's recap is not the field table.** A manual's own summary list — a 注意事項 note, a changelog, a quick-reference — can omit a field the full request table defines (NDNF-1.2.5 p.40 lists every method flag except `TWQR`, which p.38 defines). Transcribe from the table and use the recap only as a cross-check; record any difference as a finding against the recap, not the table. **Same field name, per-family numbering.** A status field several families share may number its values differently per family (NDNF `CloseStatus` 3 = 請款完成 for cards and wallets but 請款失敗 for BNPL; the payment callback's integer `StoreType` numbers OK as 3 where the logistics `ShipType` numbers it 4). Keep one value table per family keyed on the family field, refuse a value that is not on its family's table, and never derive one document's code from another's integer.

**Traffic is an authority too (2026-10-12).** Where the field crosses the wire in a flow the walk can drive,
capture it (HAR from the walk's browser, or the proxy) and set three columns side by side: what the
document says, what the code believes it sends or reads, what the traffic shows. Any disagreement is a
contradiction row (`evidence.md` §E7), not a judgement call; the reverse trace in §E10 says how.

## S5 — Control to consumer (dead control / control-to-consumer wiring)

For every admin toggle, feature flag, or settings row, grep for the runtime consumer in the user-facing path. A control with no consumer, or a consumer still reading the legacy source the control was meant to replace, is a finding. **The form is part of the control, and so is the queue.** When a gate is widened — a method that used to accept only one state now accepts two — every surface that leads to it must be widened in the same commit: the renderer that draws the button, the queue whose predicate lists the work, the filter on the desk. Widening the handler alone leaves a capability that exists, passes its unit test, and cannot be reached by the person it was built for (a dispatch control that accepted a cash-on-pickup order while the form that calls it still rendered only for `paid`). Sweep by predicate, not by method name: grep the old condition across renderers, queries and tests, and confirm each hit was considered. **The host's whitelist is a consumer.** When a module copies the request into a named field list before the controller sees it, every field the page posts and the list omits is a dead control that answers with a success notice (a `Turn ON` toggle whose `feature`/`enabled` fields were dropped by `stringsFrom()` for three weeks); a controller test that bypasses the host module proves nothing about it. Walk the whitelist against every `name=` the page renders, and treat a module that hands the request over another way as an exemption to be named, never as silence.

**S5.1 — a control's consumer can retire out from under it; the script needs its caller named, not a person who remembers to run it (2026-09-20).** A menu-grouping script (`tools/dev/refresh-admin-nav.php`) wrote the DB rows a redesigned admin menu depended on, and wrote them correctly — but its only caller was a local dev launcher (`start.ps1`) retired weeks earlier in favour of `docker compose`. Nothing was broken: the script still ran clean by hand, code review found no defect in it, and the menu simply drifted back to install order because nobody who ran the current launcher ever invoked it. **A maintenance script is a control, and a control with no live caller is dead, whatever its own test proves.** Enumerate every script under `tools/` (or the project's equivalent maintenance root) and name its live caller — a crontab line, an installer, a CI step, a deploy hook — not the developer who happens to remember it exists. A script whose only caller is a launcher, wrapper or workflow that has since been retired is the same finding as a settings toggle with no runtime reader: correct, tested, and reachable by nobody.

