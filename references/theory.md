# Theory — Stafford Beer's Viable System Model, applied to a codebase

Loaded by `cia` before §0.9 step 0 (the VSM map). The map assigns every component to one of the systems below; the sweeps then walk the channels between them.

> **THEORY: STAFFORD BEER'S VIABLE SYSTEM MODEL, APPLIED TO A CODEBASE.**
> Beer's claim (*Brain of the Firm*, 1972; *The Heart of Enterprise*, 1979) is that any system
> which survives in a changing environment has the same five-part structure, at every level of
> recursion: **System 1** does the work; **System 2** damps oscillation between the parts of
> System 1; **System 3** commands and allocates resources to System 1 and hears back through
> **System 3\***, an audit channel that bypasses System 1's own reporting; **System 4** faces the
> environment and the future; **System 5** holds identity and policy and receives the
> **algedonic** signal (pain/pleasure) that jumps every level when viability is threatened. The
> systems are connected by **channels**, and Ashby's Law of Requisite Variety says each channel
> must carry as much variety as the thing it regulates, or control is fictional.
>
> A codebase is such a system. Handlers, checkout, fulfilment are System 1. Locks, queues,
> deadlines, idempotency keys are System 2. Settings, flags, admin pages, config are System 3.
> Test suites, probes, reconciliation are System 3\*. Vendor specs, external APIs, callbacks are
> System 4. Defaults, catch-block posture, kill switches are System 5.
>
> **PRIMARY TARGET: CROSS-BOUNDARY INVARIANT VIOLATIONS**, also called **integration-level
> defects** or **emergent defects**. In Beer's terms every one of them is a broken, missing, or
> under-variety channel between two of those systems: a System 3 setting no System 1 code reads
> (dead control); a value System 1 froze at one moment while a later System 1 step re-reads System
> 3 live (stale snapshot); a predicate checked at SELECT and dropped at UPDATE with no System 2
> coordinator (TOCTOU); a System 4 field read against the code's belief rather than the vendor's
> definition (semantic drift); a System 3\* suite that reports OK because it never ran the tests
> that touch the store (vacuous pass: System 3\* reading System 3's own conclusion); a catch block
> with no System 5 policy behind it (fail-open). Each function is individually correct. Static
> analysis, linters and a green unit suite inspect one piece at a time and therefore cannot see a
> channel. This skill exists to see channels. Reading functions is not auditing; mapping the
> codebase onto Systems 1–5 (§0.9 step 0) and then tracing every channel of that map, one value
> from every writer to every reader, one control from the screen to the line that obeys it, is.
> Section 0.9 is the mandatory sweep list and runs before any other doctrine. Structure first,
> then wiring, then code.
>
> Stance, from Beer: the purpose of a system is what it does, not what its docs say (POSIWID);
> every System 1 unit is itself viable and gets the same five questions one recursion down;
> every guard is a variety attenuator and every default an amplifier, and each must match what
> it faces; System 1 must act without asking System 3 each step, yet System 3 must still be
> obeyed; the auditor *is* System 3\*, the channel that bypasses the system's own green report;
> and a pain signal that stops in a log file has not reached System 5.

---

# 2. VSM Governance Model

Assign each system component to a primary VSM role. Components may participate in multiple systems.

## System 1 — Primary Operations

Autonomous execution of core user/application workflow.

**Examples (universal):**
- command execution
- data transformation
- user interaction handling
- state mutation
- local computation
- file read/write
- rendering
- network request initiation

**Examples (Blender addon):**
- mesh operations (create, modify, delete)
- material assignment
- object transforms
- property updates
- viewport manipulation
- tool interaction
- file operations

Rule:

System 1 should complete essential work without unnecessarily blocking on:
- non-critical analytics
- reporting or dashboards
- secondary notifications
- non-essential logging
- expensive background queries

Critical synchronous consistency checks remain permitted where required for correctness.

---

## System 2 — Coordination & Anti-Oscillation

Prevents races, duplication, contradictory execution, and interference.

**Examples (universal):**
- transactional constraints
- idempotency keys
- webhook deduplication
- concurrency control (locks, CAS, MVCC)
- request deduplication
- event ordering
- undo/redo atomicity
- cancellation safety
- namespace isolation
- priority/scheduling

**Examples (Blender addon):**
- undo/redo entry atomicity (one logical operation = one undo entry)
- modal state (prevent nested dialogs)
- mesh modifier ordering (prevent conflicting modifications)
- material update deduplication (avoid double-applying material)
- addon hook ordering (if multiple addons hook the same event)
- timer/event loop sequencing
- property write conflicts (two addons modifying same object)
- asset import deduplication

Primary question:

> What prevents two individually valid operations from creating an invalid combined result?

---

## System 3 — Control & Internal Synergy

Maintains authoritative operational state and data model.

**Examples (universal):**
- object/entity state
- property/attribute values
- relationships between objects
- transaction ledger
- execution state
- data schema
- serialized form (file, database)

**Examples (Blender addon):**
- scene object hierarchy (Blender's data model)
- addon-maintained state (separate from Blender's, if any)
- undo stack (as authoritative for operation reversibility)
- file serialization format (how addon data persists)
- dependency graph (object A depends on B, which depends on texture C)
- modal state (which dialog is active)
- cache (processed data derived from authoritative state)

Primary question:

> Where is authoritative state held, and how do all subsystems converge toward it?

---

## System 3* — Independent Audit Channel

Verifies that reported operational state corresponds to reality through external evidence.

**Examples (universal):**
- file-system audit (expected files exist with correct permissions)
- API verification (query actual API state vs. local representation)
- checksum validation
- immutable audit logs
- external event ledgers
- state-recovery tests

**Examples (Blender addon):**
- scene consistency checker (orphaned references, broken material links)
- undo stack validation (can every entry be replayed without error?)
- asset reference audit (are all textures/models available on disk?)
- serialization round-trip test (save → load → compare to original)
- viewport state match (displayed material vs. actual scene data)
- object hierarchy audit (no circular references, orphaned objects)

System 3* must not merely read System 3's own conclusion and call that an audit.

Where practical, compare independent evidence:

**Example (Blender):**
- Internal addon state: material assigned
- Blender scene query: object.active_material == material
- Undo stack replay: undo returns to pre-assignment state
- Viewport: material visibly applied

---

## System 4 — Intelligence & Adaptation

External sensing and future adaptation; informs operations without blocking live execution.

**Examples (universal):**
- performance monitoring (latency, memory, CPU)
- user behavior analytics (common workflows, error patterns)
- error rate tracking
- external system status (API availability, version changes)
- forecasting (resource needs, upcoming changes)
- library/dependency updates
- compatibility checks

**Examples (Blender addon):**
- performance monitoring (slow mesh operations, memory leaks)
- user workflow patterns (which features are most used)
- Blender version compatibility (are newer APIs available?)
- external asset sources (library updates, new textures available)
- GPU memory tracking
- render time forecasting

---

## System 5 — Policy, Identity & Emergency Control

Ultimate policy authority and emergency intervention.

**Examples (universal):**
- authentication and authorization
- data access policies
- error handling policies
- failure scenarios (what to do on timeout, network error, etc.)
- privacy and security policies
- shutdown/cancellation behavior
- recovery procedures
- permission levels
- audit logging policies

**Examples (Blender addon):**
- addon stability tier (alpha/beta/stable)
- Blender version requirements (min/max)
- cancellation behavior (ESC key, cleanup on user interrupt)
- data backup policy (save before destructive operations)
- conflict resolution (what if two addons try to modify the same object?)
- undo limit (max undo stack depth)
- permission model (which operations require admin/elevated mode?)
- emergency disable (can addon be disabled if causing crashes?)

System 5 receives **algedonic alerts** (pain signals) when system viability is threatened.


---

# 16. Quick Reference: VSM System Mapping

When reporting findings, classify by system:

| System | Focus | Example Finding |
|--------|-------|-----------------|
| 1 | Execution speed, user experience | "Texture load blocks UI for 5 seconds" |
| 2 | Races, deduplication, ordering | "Two undo requests can collide; mesh state undefined" |
| 3 | Authoritative state, consistency | "Material deleted but addon still references it; no recovery" |
| 3* | Verification, audit trails | "No way to detect if undo stack corrupted" |
| 4 | Monitoring, adaptation | "No metrics on slowest operations; can't forecast load" |
| 5 | Policy, emergency control | "No way to disable addon if crashing; requires Blender restart" |

