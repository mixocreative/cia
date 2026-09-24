# Reporting — finding format, severity, verified controls, final report, behavioural rules, worked example (§9–§13, §17)

Loaded by `cia` before writing any finding and before the Step 6 report.

# 9. Required Finding Format

Every reported issue must contain:

## ID
Unique audit finding identifier (e.g., `BLA-001`, `ECOM-025`).

## Severity
- **CRITICAL**: Data loss, unauthorized access, financial loss, or system crash
- **HIGH**: Serious correctness or security defect under realistic conditions
- **MEDIUM**: Important defect without immediate catastrophic consequence
- **LOW**: Edge case, maintainability, or minor inconsistency
- **INFORMATIONAL**: Improvement or verified design note without identified defect

**The primary path, named first.** Every system has one unit of work it exists to get right —
the payment in a shop, the job execution in a runner, the record in a store, the message in a
queue, the alert in a monitor — and one or more *safety nets* watching it (the monitor, the
reconcile, the watchdog, the test suite). Name that unit in the invariant register before
grading anything; the floor below is written against it. **This skill is universal: "primary
path" is not a synonym for "money path".** Three fixture runs in a row (2026-09-15 to
2026-09-19) graded the same two rows one level low on a job runner because the floor said
"money" and the auditor could not see money.

**The floor, from those runs:** a defect on the primary path or a safety net is graded by **what
happens to the unit of work or the person when it fires**, not by how small the code is. *The
unit lost, executed twice, or recorded as finished when it was not — with no notice* is
**CRITICAL**, even when the fix is one predicate: an `UPDATE … WHERE id = ?` that lets two
workers claim one job or a payment be overwritten as expired, a `catch` that answers "received"
while the write failed, a verify that returns true on its own exception. A race whose divergence
nothing detects is "undetectable state divergence" (§10), which is CRITICAL — "race condition
leading to inconsistency" (HIGH) is the race a later check *would* notice. *A person cannot see
or act on a primary-path state* (an unrendered terminal state, an alarm that reaches a log) is
**HIGH**, never MEDIUM. *A detector that cannot tell blind from clean* on the primary path is
**HIGH**. *A test that proves nothing* on the primary path **or on a safety net** — a monitor
whose only test asserts it found nothing — is **HIGH**, because every earlier green it produced
was a claim. MEDIUM is for defects with a working fallback or a person already in the loop; LOW
is for what costs nothing when it fires. When in doubt between two grades on the primary path,
the higher one is right — an under-graded primary-path defect is the one that ships.

**Grading is not filing — the promotion rule.** An observation that stayed in step prose has not
been reported. Two runs of the same doctrine on the same fixture (`tests/RUNS.md`, 2026-09-20)
scored 10/10 and 6/10; all three of the cheaper run's misses were promotion failures, not
discovery failures — it named the fail-open catch, the unread heartbeat and the assert-nothing
test in its own narrative and filed none of them as findings. The doctrine was identical. Only
the reporting reflex differed, and the 10/10 run got that reflex from a sentence in the harness
prompt rather than from this file, which is the instrument scoring its own scaffolding. So the
sentence lives here now:

**Every observation that meets a threshold above becomes a numbered finding — an ID, a grade, a
`path:line` and the invariant it violates — in the same pass that saw it.** "Noted", "worth
checking", "could be tightened", and a clause inside a step description are not findings and do
not count as reported. An observation that does *not* meet a threshold still gets a sentence
naming the grade it failed to reach; ungraded prose is how a real defect leaves an audit. When
the auditor cannot decide whether a threshold is met, it is met: file at the higher grade with
confidence POSSIBLE and let the fix-or-escalate pass settle it. Filing costs a paragraph. Not
filing costs the defect.

**And a site in a sweep line is not a finding.** The first cold run of the live fixture
(2026-09-24) listed `public/index.php:91-93` — the checkout quantity, "`(int)` cast, no bounds"
— among the sites of its S11 line, and never filed the defect. A customer ordering `-3` raised
the shop's stock and wrote a negative total, and the audit had *looked straight at it*. Sweep
lines enumerate where you looked; the findings list is what you found. A site that met a
threshold and appears only in the enumeration is the same miss as one nobody visited, and it is
harder to notice because the line looks thorough.

## Confidence
- **CONFIRMED**: Defect demonstrated from code, logs, or tests
- **HIGH-CONFIDENCE**: Strong evidence but runtime confirmation unavailable
- **POSSIBLE**: Control could not be verified

## VSM Classification
System 1 / 2 / 3 / 3* / 4 / 5

## Domain
State Management, Concurrency, API Contracts, Persistence, Extensibility, Security, UI/UX, i18n, etc.

## Defect Class
The §0.9 taxonomy term (TOCTOU race, temporal coupling / stale snapshot, semantic drift, dead control, fail-open default, vacuous pass, deferred-work residue, rename residue, boundary schema drift, cascade / retry storm, or "single-component" when the defect is not cross-boundary).

## Boundary Location
The two sides the defect lives between, as `producer → consumer` or `Step N (what) → Step N+1 (what)`. Examples: `Checkout::placeOrder (deadline frozen) → OrderDesk::offeredMethods (settings re-read)`, `gateway callback parser → SelfHealDecision`. Add the VSM channel the defect sits on, e.g. `System 3 → System 1`, `System 3* → System 3`, `System 4 ↔ vendor`. "None" is acceptable only when Defect Class is single-component.

## Invariant
What must remain true (the rule being violated).

## Evidence
Exact location:
- File name and line number
- Function / class name
- API endpoint
- Schema field
- UI element
- Configuration key
- Provider documentation version

## Observed Behavior
What the system currently does (factual, not interpretive).

## Failure Scenario
Concrete, reproducible sequence that triggers the bug.

**Example:**
```
1. User creates Sphere mesh
2. Addon applies boolean modifier
3. While modifier evaluating, user presses Undo
4. Result: mesh is neither original nor boolean result; in invalid state
```

## Impact (emergent)
What fails downstream as a result, then customer/user consequence, operational impact, financial impact.

## Recommended Fix
Technology-appropriate remediation (not over-engineered).

## Verification Test
How to prove the defect is fixed.

---

# 10. Severity & Impact Model

## Critical Severity Indicators

Likely or demonstrated:
- Financial loss or unauthorized charges
- Unauthorized access to sensitive data
- Complete data loss or irrecoverable corruption
- Systemic overselling or over-redemption
- Payment forgery or double-charge
- Privilege escalation
- System crash or denial of service
- Undetectable state divergence

---

## High Severity Indicators

Serious transactional or operational corruption under realistic conditions:
- Partial data loss (recoverable with effort)
- Race condition leading to inconsistency **that a later check or a person would notice** (one nothing notices is CRITICAL — undetectable state divergence, above)
- Failed idempotency (duplicate operations produce different results) — when the duplicate is the primary unit of work executed twice with no notice, CRITICAL
- Unhandled third-party outage (no fallback or retry)
- Missing audit trail for critical operations
- Recovery procedure is manual and error-prone

---

## Medium Severity Indicators

Important correctness, recovery, UX, or admin defect without immediate catastrophe:
- UI mismatch with backend state
- Confusing error message (user unsure what to do)
- Recovery is possible but requires steps
- Stale cache not refreshed on mutation
- Missing localization (English-only in multi-language app)
- Timeout handling could be more robust

---

## Low Severity Indicators

Limited edge case, maintainability, or minor inconsistency:
- Rare race condition (requires perfect timing)
- Typo in non-critical string
- Log message could be clearer
- Performance could be optimized
- Dead code or unused variable

---

## Informational

Improvement or verified design note without an identified defect:
- Callback validation confirmed and correct
- Idempotency key correctly used throughout
- Recovery procedure well-documented
- Verified that addon isolation prevents interference
- Good practice observed (suggest documenting for future audits)

---

# 11. Verified Controls

Do not produce only negative findings.

Record important controls proven to be correct. This prevents repeated audits from re-auditing already verified architecture.

**Examples (universal):**
- Idempotency key enforced on all sensitive operations
- Database transactions ensure atomicity
- Webhook signature validation confirmed
- Retry logic prevents duplicates
- Concurrent access to same resource uses lock/CAS/MVCC correctly

**Examples (Blender addon):**
- Material assignment is atomic (one undo entry)
- Undo stack replay is deterministic
- Deleted object references cleaned up on undo
- Addon namespace isolated (no collision with other addons)
- Cancellation releases all resources within 100ms

**Examples (e-commerce):**
- Payment callback deduplication prevents double-charge
- Inventory reservation locked for correct duration
- Refund atomicity (payment + inventory + ledger all succeed/fail together)
- Invoice reconciliation audits against payment gateway
- Tax calculation deterministic across retries

---

# 11a. The Evidence Ledger — capability × verdict × artefact

Verified controls (§11) say what the auditor believes after reading. The ledger says what
the run can **prove**. It is one table, it appears in every report, and it is the only place in
this doctrine where a paragraph of correct source code counts for nothing.

**Rows.** Every capability the system claims, taken from the §0.9 step-0 map: one row per
System 1 unit of work, plus one per System 2 / 3 / 3* / 4 channel that unit depends on. The map
fixes the row list, so the ledger cannot be narrower than the system. For a commerce system the
sibling `ecommerce-cia` fixes a mandatory row list on top of this one.

**Columns.**

| Capability | Verdict | Evidence (artefact path) | What the evidence shows |
|---|---|---|---|

**Verdicts, and the only things that produce them:**

- **PASS** — an artefact produced *by this run* shows the capability behaving correctly, end to
  end. An artefact is a file on disk or a command output captured this session: a test runner's
  line naming the test that ran, an HTTP status with the response, a stored row read back after
  the operation, a screenshot, a log line with its timestamp. `browser-walks.md` §14 fixes what
  each kind of artefact is allowed to prove.
- **FAIL** — an artefact shows it behaving incorrectly. A FAIL row carries the finding ID.
- **UNVERIFIED** — everything else: no artefact, an artefact from an earlier run, an artefact
  that proves a neighbouring fact, or a capability this tier excluded.
- **UNPROVEN** — the run tried, reached the system, and **could not tell**: the environment was
  down, the shop was in maintenance, the session dropped, a redirect went to a login, every retry
  hit the same wall. Added 2026-09-24, because folding this into UNVERIFIED loses the distinction
  a reader needs most. UNVERIFIED reads as *not attempted*; "skipped" reads as *deliberately
  excluded*; this is **"I attempted it and the environment would not let me answer"**, and it is the
  only one of the three that should stop a green light on its own, because nobody knows what is
  behind it. The evidence column names what blocked it and how many attempts agreed.

**Three artefact rules that belong with UNPROVEN, because each is a way an environment failure gets
recorded as a fact about the code:**

- **An environment outcome is never a defect row.** A tool that fetches many pages must distinguish
  *this row is broken* from *the server was unreachable / the site was closed / I was redirected to
  a login*. Without that split, one concurrent maintenance toggle produces a page-long list of
  false defects against exactly the surface somebody is about to work from — and the list is
  indistinguishable from a real one.
- **A 200 that renders an exception inside the layout is a FAIL, not a PASS.** The status code is
  the transport's opinion. Assert on the body: a framework error page, a stack trace, an untemplated
  exception string or an empty main region returned with a 200 is the most common way a broken page
  is counted as a working one.
- **A retry that succeeded is reported as a retry.** `PASS (attempt 2)`, never folded into the green
  count. A capability that needs two attempts is a different fact from one that needs one, and the
  folding is how an intermittent failure becomes invisible in exactly the report that should have
  named it.

**The rule that gives the ledger its value: reading the source can never produce PASS.** Not
"the code clearly does this", not "the test for it exists", not "the handler is registered", not
"I traced every branch". That is how a defect is *found*; it is not how a capability is
*proved*. An auditor who has read a capability's whole implementation and run nothing against it
writes UNVERIFIED and is right to. The ledger is deliberately harsher than everything else in
this skill, because everything else rewards good reading, and the ledger exists to measure the
thing reading cannot reach.

**UNVERIFIED is a result, not an apology.** A report with twelve honest UNVERIFIED rows and a
named tier is worth more than one with twelve PASS rows a reader cannot check. What is forbidden
is the promotion: an UNVERIFIED cell that becomes PASS because the auditor later read more code,
because a neighbouring capability passed, or because the suite is green overall. A green suite
promotes the rows whose *named tests* ran, and promotes nothing else.

**No blank cells, no omitted rows.** A capability with nothing to say is UNVERIFIED with the
reason in the evidence column ("tier: Screen, not walked"; "no environment - §0.8 rung 5: <the
one thing the owner must do>"). A capability the system does not have is `N/A` with the reason.
An omitted row is the report claiming a smaller system than the map found, which is S14 scope
shadow committed by the auditor.

**A PASS covers the capability's refusals, not only its successes.** The same run marked
`Checkout` PASS on two artefacts — a valid order created, an over-quantity order refused — while
a negative quantity on that same route raised stock and wrote a negative total. Both artefacts
were real, the row was still wrong: the capability is *checkout*, and the auditor had exercised
two of its paths. So every PASS row's fourth column says **what the artefact covered**, in the
capability's own terms ("valid order; over-quantity refused" — at which point the reader sees
what is missing), and a capability exercised only on its happy path is **PARTIAL**, which is
read as UNVERIFIED by anyone deciding whether to launch. The honest question before writing PASS
is not "did it work?" but "which of this capability's ways of being asked did I ask?"

**Where the rows come from, and the order they are written in:** the ledger is built at the
*start* of the runtime steps, all rows UNVERIFIED, and filled as artefacts arrive. Built at the
end, it is written from memory, and memory is where PASS comes from reading.

**And prove the artefact landed, because the tool that stores it can succeed at doing nothing
(2026-09-24, proved).** A session wrote its walk artefacts to a new top-level `walks/` directory and
`git add walks/…` silently no-opped: a generic `walks/` pattern in the machine's **global** ignore
file, `~/.gitignore_global`, outside the repository and invisible to any amount of reading the
repository's own `.gitignore`. The commit would have landed empty and read as success. So: **any
run that creates a new top-level directory for its evidence runs `git check-ignore -v <dir>` before
believing its own commit**, and every claim that an artefact was stored is checked by reading it
back from where it was meant to land — `git show --stat`, `ls` the path, re-open the file. The
general form is the one to carry: *the rule that bites is the one outside the artefact you are
reading.*

---

# 12. Final Audit Report Structure

Always organize findings into **five sections**:

## 1. Systemic Risks & Algedonic Signals

Only true showstoppers or severe systemic threats.

Prioritize:
- Money (unauthorized charges, loss of revenue, fraud)
- Authorization (unauthorized access)
- Data integrity (unrecoverable corruption, permanent loss)
- Availability (system down, unable to recover)
- Compliance (violates law, policy)

---

## 2. State Machine & Consistency Gaps

Show mismatches among:
- User interface state
- Backend/database state
- External system state (payment provider, logistics, file system)
- Undo/redo stack
- Audit logs

Explain the invalid transition or missing state.

---

## 3. Failure Handling & Recovery Gaps

Include:
- What happens if third-party times out?
- What happens if user cancels mid-operation?
- What happens if system crashes (recovery procedure)?
- What happens if operation is retried?
- Are error messages actionable?
- Is manual recovery documented?

---

## 4. Verified Correct Controls

List high-value controls verified from evidence.

Do not give generic praise. Cite specific architecture:
```
✓ Payment idempotency: All payment operations keyed by transaction ID;
  duplicate webhook processed exactly once (verified in payment handler, line 342)
  
✓ Undo stack atomicity: Each user action becomes one undo entry;
  no partial undo entries observable (verified via test matrix, Concurrent test)
```

---

## 5. Concrete Action Plan

Prioritize fixes by impact and effort:

### P0 — Stop the Line
Immediate integrity/security fixes. Block deployment/use until resolved.

### P1 — Required Before Production
Major correctness/recovery issues. Must fix before live release.

### P2 — Operational Completeness
Admin recovery, edge states, missing procedures. Fix before sustained use.

### P3 — Hardening / UX / Optimization
Non-blocking improvements. Backlog for next iteration.

For each item, specify:
- Component/file affected
- Specific change required
- Expected invariant after fix
- Verification test (how to prove it's fixed)

---

# 13. Auditor Behavioral Rules

You **must**:

- Trace actual execution flows (don't assume from architecture diagrams)
- Inspect implementation evidence (code, logs, tests, actual behavior)
- Reconstruct state machines (what states are possible? what transitions?)
- Identify systems of record (where is authoritative state?)
- Test concurrency scenarios logically (races, timeouts, retries)
- Separate orthogonal concerns (payment from fulfillment, state from rendering)
- Distinguish user-visible outcome from authoritative state
- Recognize eventual consistency (system may be temporarily inconsistent)
- Verify external facts against current documentation/API versions
- Adapt to context (Blender addon constraints differ from SaaS constraints)
- Identify missing admin/recovery procedures
- Report verified controls (not just problems)
- Map findings to VSM systems (not just list issues)

You **must not**:

- Assume default/mainstream behavior everywhere (Stripe payment isn't universal, SQL isn't everywhere, undo isn't guaranteed)
- Assume specific technologies are mandatory (Redis, S3, Postgres, etc.)
- Assume success paths without testing failure paths
- Generate speculative vulnerabilities without evidence
- Recommend architectural complexity without demonstrated need
- Assume user input is always well-formed
- Assume network is reliable
- Assume single-threaded execution (even if appears to be)
- Assume provider behavior from memory (check docs)
- Assume one version of standard applies globally (tax, payment APIs, dates)
- Confuse UI state with authoritative state
- Report "best practice" violations without demonstrating actual harm
- Overlook recovery procedures (focus on detection + recovery, not prevention only)

## Nothing leaves the room unrecorded, and the record lives where the next person will trip over it

An audit finds more than it can responsibly change in one sitting, and deciding not to act is
often the right call — a fix riding on top of a load-bearing change makes both harder to attribute
if something moves, and a latent defect that costs nothing until a particular future edit is a
poor use of the same attention. **What makes that a decision rather than an oversight is where the
note lands.**

Three instances from one day, arrived at independently: an auditor holding a queue of doctrine
edits rather than changing the tree its own validation runs were being scored against; a set of
real findings parked with an explicit ruling in a ledger rather than fixed mid-flight; and a
counted, latent inconsistency recorded instead of repaired because repairing it was its own change.
All three were correct, and all three were correct for the same reason.

**The rule is not "fix everything". It is: nothing leaves the room unrecorded, and the record goes
where the next person will trip over it, not where the author would look for it.** A note in a
commit message nobody greps is dropped. A note in the auditor's own head is dropped. A note at the
place the change would be made — beside the enumeration that will drift, in the file the next
editor opens, in the register row the next audit reads first — is deferred, and deferred is a
position a reader can disagree with.

So for every finding this run does not act on, the report says three things: **what it is, why it
was not done now, and where the note lives.** A deferred finding with no third answer is an
undeferred one.


---

# 17. Examples: From Generic to Specific

### Incomplete Finding (Generic)
> "Concurrency issue exists in payment processing."

### Complete Finding (Specific)
```
ID: ECOM-042
Severity: CRITICAL
Confidence: CONFIRMED
VSM System: 2 (Coordination)
Domain: Concurrency & Atomicity

Invariant: Coupon with limit of 5 redemptions cannot be redeemed 6 times

Evidence: 
  File: checkout/coupon.py, lines 145-160
  Query: SELECT count(*) FROM orders WHERE coupon_id = ?
  Update: UPDATE coupons SET redeemed = redeemed + 1 WHERE id = ?
  
Observed: SELECT and UPDATE are not atomic; gap between check and update

Failure Scenario:
  1. Coupon has 4 redemptions (limit 5)
  2. Customer A and B simultaneously checkout with coupon
  3. Both SELECTs execute, both see count = 4 (< 5), both proceed
  4. Both UPDATEs execute: redeemed becomes 6
  5. Coupon over-redeemed; business loss

Impact: Revenue loss; exceeded promotional budget; customer trust

Recommended Fix: Use atomic SQL:
  UPDATE coupons SET redeemed = redeemed + 1 
  WHERE id = ? AND redeemed < limit
  Check affected rows = 1; if 0, reject

Verification: Load test with 100 concurrent requests; coupon never exceeds limit
```

---

**Reading receipt: _the ledger is harsher on purpose_.** Quote this phrase on the Step 6 receipts line to show this
file was read rather than inferred from the skill's index. It appears nowhere else.
