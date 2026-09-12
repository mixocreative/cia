# Audit Doctrine — evidence, context discovery, test matrix, domain checklist

Loaded by `cia` at Step 2 after the sweeps. Sections keep their original numbers (§1, §3, §7, §8) because findings and project registers cite them.

# 1. Fundamental Audit Doctrine

## 1.1 Audit Outcomes, Not Implementation Details

Never mark an implementation defective solely because it does not use a technology you expected.

Examples:

**Do not** require Redis for concurrency.
A transactional SQL operation, compare-and-swap, row lock, optimistic concurrency control, distributed lock, or another correctly implemented mechanism may be equally valid.

**Do not** require a specific serialization format.
JSON, MessagePack, Protocol Buffers, or database-native serialization may satisfy the same persistence invariant.

**Do not** require a specific UI framework.
Qt, GTK, Electron, web-based, or native platform APIs may implement the same user interaction contract equally well.

**Do not** require specific state management.
Event sourcing, CRDT, MVCC, application-level undo stacks, or external version control may preserve the same invariants.

Audit the **invariant**, not the technology brand.

---

## 1.2 Evidence Before Accusation

Every technical finding must distinguish between:

### CONFIRMED
The failure path is demonstrated from code, schema, configuration, test behavior, logs, API documentation, or authoritative platform documentation.

### HIGH-CONFIDENCE
The implementation strongly indicates the defect but runtime confirmation is unavailable (e.g., code review shows race condition logic without ability to trigger it).

### POSSIBLE
A required control could not be located or verified (e.g., "cancellation cleanup mechanism not found in available source").

Never report:

> "Redis is missing, therefore race condition exists."

Instead report:

> "Property writes are checked before update without atomic assignment, versioning, or compare-and-swap. Two simultaneous modifications can therefore both observe the same prior state and write conflicting values."

---

## 1.3 External Facts Must Be Version-Aware

APIs, file formats, platform capabilities, tax laws, security standards, rendering pipelines, and plugin interfaces change.

When documentation/API access is available:

1. Identify system and version (e.g., Blender 4.0, Stripe API 2024-01-15, n8n 1.45)
2. Consult current official platform/provider documentation
3. Consult current official standards or regulatory sources
4. Compare actual implementation against requirements
5. Note version cutoff if auditing against older docs

Source precedence:

1. Current official platform/provider documentation
2. Current official standards/laws/regulations
3. Application source code and data model
4. Documented policies or configuration
5. Reliable secondary material
6. Inference from behavior

Never permanently hard-code temporary API limits into audit doctrine.

Example:

**Do not assume:**
> "Blender material slots always have a 64-slot maximum."

**Instead audit:**
> "Does this addon respect Blender's current material slot limits and gracefully handle the case where a material cannot be assigned?"


## 1.4 External facts are fetched fresh, and their location is recorded

Before deciding anything that depends on a third party — a vendor field's meaning, an API
limit, a protocol rule, a price — look for the vendor's latest official document first (on
disk, then the vendor's own site), cite the version and the date read, and record where it
was found in the project's reference file (`docs/integrations/vendor-doc-locations.md` or the
project's equivalent: portal URL, document name + version on disk, fetch quirks such as a
required browser User-Agent, date last seen). A fact from memory, from a code comment, from an
old screenshot or from a third-party rendering while the original is reachable is unverified.
For a vendor the project has never recorded, search for its official portal (own domain, then
its GitHub organisation, then a regulator or standards page) and record it before use. A newer
document than the one the code was audited against is not a defect; not having diffed its
changelog against what the code sends and parses is.

---

# 3. Context Discovery — Do This Before Judging the System

Establish an **Audit Profile** before diving into implementation details.

## 3.1 Software Type

- [ ] Desktop application (standalone)
- [ ] Web application (single server or distributed)
- [ ] Plugin / Addon / Extension (Blender, Maya, VS Code, Unreal, etc.)
- [ ] Mobile application (iOS / Android)
- [ ] CLI tool / daemon
- [ ] Library / SDK
- [ ] Workflow orchestration (n8n, Zapier, etc.)
- [ ] API service / microservice
- [ ] Custom / hybrid

---

## 3.2 State Scope & User Model

- [ ] Single-user, local state only (offline-first)
- [ ] Single-user, cloud-backed state (sync to server)
- [ ] Multi-user, turn-based collaboration (user A → user B)
- [ ] Multi-user, real-time collaboration (simultaneous editing)
- [ ] Server-side only (client is stateless)
- [ ] Distributed state (multiple services, eventual consistency)

---

## 3.3 External Dependencies

List all systems that can fail independently:

- [ ] File system (local or network)
- [ ] Database (SQL, NoSQL, or cloud)
- [ ] APIs (REST, GraphQL, webhooks)
- [ ] Authentication provider (OIDC, OAuth, LDAP)
- [ ] Payment provider
- [ ] Rendering engine (GPU, cloud render farm)
- [ ] Other addons / plugins / extensions
- [ ] Third-party services (CDN, analytics, logging)
- [ ] User input device (mouse, keyboard, VR)
- [ ] Clipboard / drag-and-drop
- [ ] Networking (LAN, internet)

---

## 3.4 Persistence Mechanisms

How is state preserved across crashes, restarts, or closes?

- [ ] Undo/redo stack (volatile, lost on crash)
- [ ] File format (JSON, XML, binary, custom)
- [ ] Database transactions (ACID guarantees)
- [ ] Cloud sync (automatic or manual)
- [ ] Checkpoint/snapshot (periodic state capture)
- [ ] Event log (append-only, replay-able)
- [ ] Git / version control integration
- [ ] None (state is ephemeral)

---

## 3.5 Concurrency Model

- [ ] Single-threaded, event-loop driven (no true parallelism)
- [ ] Multi-threaded with mutex/lock-based synchronization
- [ ] Multi-threaded with lock-free data structures (CAS, atomic)
- [ ] Async/await (promise-based concurrency)
- [ ] GPU compute (asynchronous, parallel execution)
- [ ] Distributed systems (eventual consistency, quorum)
- [ ] Real-time constraints (hard deadlines)

---

## 3.6 Failure Tolerance & Recovery

- [ ] Transactional (all-or-nothing)
- [ ] Idempotent (safe to retry)
- [ ] Compensating transactions (undo via reverse operation)
- [ ] Checkpoint-based (resume from last good state)
- [ ] Manual recovery (human intervention required)
- [ ] Eventual consistency (asynchronous recovery)


---

# 7. Universal Test Matrix

For every critical transaction flow, test at least:

## Happy Path
Normal, expected sequence with all systems responding correctly.

**Example (Blender addon):** Create mesh → apply modifier → save file → reopen.

**Example (e-commerce):** Add item → checkout → payment success → order confirmed.

---

## Duplicate
Same request/event delivered twice.

**Example (Blender addon):** User hits operator twice by accident (or click handler fires twice).

**Example (e-commerce):** Customer clicks "Pay" twice before form disables; gateway processes both.

**Example (workflow):** Webhook from Slack fires twice (timeout + retry).

---

## Concurrent
Two conflicting valid operations executed simultaneously.

**Example (Blender addon):** Two addons modify same mesh property at same time.

**Example (e-commerce):** Customer and admin both issue refund simultaneously.

**Example (workflow):** Two parallel branches both try to update same record.

---

## Timeout
Remote operation may have succeeded while local operation timed out.

**Example (Blender addon):** Texture load from network times out mid-operation.

**Example (e-commerce):** Payment gateway takes 30s to respond; customer clicks cancel after 10s.

**Example (workflow):** API call takes >60s timeout; is operation retried? Already performed?

---

## Retry
Same operation executed again after initial failure.

**Example (Blender addon):** Undo fails (scene corrupted), user tries undo again.

**Example (e-commerce):** Payment failed (temporary network error); customer retries.

**Example (workflow):** API returned 500; workflow automatically retried.

---

## Reordering
Events arrive in unexpected sequence.

**Example (Blender addon):** Undo/redo replayed in non-sequential order.

**Example (e-commerce):** Invoice received before payment webhook processed.

**Example (workflow):** Webhook arrives before database write completes.

---

## Partial Failure
One subsystem succeeds while another fails.

**Example (Blender addon):** Material updated but viewport shader not recompiled.

**Example (e-commerce):** Payment captured but inventory not decremented; customer charged but no order.

**Example (workflow):** Email sent but database write failed.

---

## Abandonment
User cancels operation mid-way (closes window, hits ESC, disconnects).

**Example (Blender addon):** User cancels long mesh operation (must clean up locks).

**Example (e-commerce):** Customer closes browser during checkout.

**Example (workflow):** Workflow paused by user; what happens to in-flight API calls?

---

## Collision (Admin or External)
External change while operation in-flight.

**Example (Blender addon):** User manually deletes material while addon UI still references it.

**Example (e-commerce):** Admin issues refund while customer initiates new payment.

**Example (workflow):** User edits workflow while execution in-progress.

---

## Stale Data
Operation uses data that has changed since it was read.

**Example (Blender addon):** Addon cached mesh data, but user modifies mesh externally.

**Example (e-commerce):** Customer views price, price changes, then completes checkout at old price.

**Example (workflow):** Template variable changed mid-execution.

---

## Provider Outage
Third-party system temporarily unavailable.

**Example (Blender addon):** Asset library offline, texture can't download.

**Example (e-commerce):** Payment gateway returns 503 Service Unavailable.

**Example (workflow):** Slack API unavailable, message can't send.

---

## Recovery
System eventually reconciles despite failures.

**Example (Blender addon):** Crash during save; reopen file and data is intact.

**Example (e-commerce):** Payment captured but email failed; reconciliation finds and retries email.

**Example (workflow):** Execution log correctly shows what succeeded and what failed.

---

## Apply to Critical Flows

For each critical user/system flow, execute the full test matrix:

**Blender addon:**
- Mesh creation with modifiers
- Material workflow (create, assign, edit)
- Asset import / file save / file load
- Undo / redo (especially after crashes)
- Addon enable / disable
- Batch operations (apply modifier to 100 objects)

**E-commerce:**
- Paid checkout (start to finish)
- Free/promotional content acquisition
- Coupon redemption
- Refund workflow
- Async payment (payment pending → settled)
- Inventory contention (last item, two customers)
- Tax calculation and invoice issuance

**Workflow:**
- Webhook trigger to multi-step execution
- Async operation (fire-and-forget, check status later)
- Error branch (operation fails, fallback executes)
- Parallel execution (multiple branches)
- Retry scenario (one node fails 3 times, then succeeds)


---

# 8. Domain Audit Checklist

Choose relevant domains for your system:

## State Management & Data Integrity

- Is authoritative state clearly identified?
- Can state diverge between subsystems (e.g., cache vs. database)?
- How is divergence detected and reconciled?
- Are concurrent writes to the same object prevented or merged?
- Is state serialization round-trip safe (write + read = same)?
- Are deleted object references cleaned up (no dangling pointers)?
- Is rollback/undo deterministic (can replay exact previous state)?

---

## Concurrency & Atomicity

- Which operations must be atomic (all-or-nothing)?
- Are non-atomic operations marked as such (best-effort, eventual)?
- Can two simultaneous requests create an inconsistent result?
- Is idempotency enforced (safe to retry without duplication)?
- Are locks/mutexes acquired in consistent order (no deadlock)?
- Is there a timeout on locks (prevent indefinite stalls)?
- Can cancellation release all locks promptly?

---

## API Contracts & External Dependencies

- Is API versioning documented?
- Are breaking changes handled (adapter layer, deprecation path)?
- Can API provider change behavior (new rate limits, new fields)?
- What happens if provider is temporarily unavailable (timeout, fallback)?
- Is every callback/webhook signature verified (replay attack protection)?
- Are callbacks idempotent (can replay safely)?
- Is sensitive data in logs/errors/metrics (audit for PII)?

---

## Persistence & Recovery

- How is state saved (file, database, both)?
- Is save atomic (crash mid-save doesn't corrupt)?
- Can recovered state be verified (checksum, schema validation)?
- Is undo/redo preserved across restarts (or intentionally discarded)?
- Are temporary files cleaned up (no disk space leak)?
- Is backup/restore tested (not just written)?
- Can data migrate between versions/formats?

---

## Extensibility & Plugin Safety

- Do plugins run in isolated namespace (no name collision)?
- Can plugins interfere with each other (shared state, event ordering)?
- Can plugins crash the host (exception handling, sandbox)?
- Are plugins versioned (what if plugin version incompatible with host)?
- Is plugin load/unload order deterministic?
- Can plugin disable/enable without restart?
- Are plugin permissions checked (can untrusted plugin access sensitive data)?

---

## Cancellation & Cleanup

- Can user cancel operation at any point?
- Is cleanup guaranteed (temp files, locks, connections)?
- Can cancellation timeout (hung cleanup)?
- Are cancel signals propagated to background tasks?
- Is cancel logged (for debugging)?
- Can operation resume after cancel, or must it restart?

---

## Security & Authorization

- Are user permissions checked before operation (not after)?
- Is object ownership verified (prevent IDOR)?
- Are secrets (keys, tokens, passwords) stored securely (not in logs)?
- Is input validated (reject malicious data)?
- Are all API endpoints authenticated?
- Is rate limiting enforced (prevent abuse)?
- Are error messages safe (no stack traces, credentials, paths)?

---

## UI/UX & Feedback

- Are pending states shown (loading, in-progress)?
- Are errors clearly explained (not cryptic codes)?
- Can user cancel in-progress operation?
- Is retry available after failure?
- Are confirmations required for destructive operations?
- Does UI match backend state (not stale data)?
- Are modals cancellable (not trapped)?

---

## i18n & Localization

- Are all user-facing strings externalized?
- Are strings translated (or placeholder obvious)?
- Do translations fit UI (text overflow)?
- Are numbers formatted by locale (1000.50 vs 1.000,50)?
- Are dates/times locale-aware?
- Are RTL languages supported?
- Are symbols/icons culturally appropriate?

