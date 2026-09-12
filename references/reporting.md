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
- Race condition leading to inconsistency
- Failed idempotency (duplicate operations produce different results)
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

