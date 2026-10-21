# Context Templates — §4 Blender addon, §4a creative / editor tool, §5 e-commerce platform, §6 workflow orchestration

Loaded by `cia` when §3 context discovery matches one of these system types. Each template restates Systems 1–5 for that shape of system; a system that matches none is profiled from §3 alone. The templates are peers: none is the default, and the order is not a priority.

# 4. Context Template: Blender Addon / Extension

Use this when auditing a Blender addon, modifier, or extension.

## Audit Profile

```
Software Type: Plugin / Addon
State Scope: Single-user local state (optionally cloud-backed asset library)
Concurrency: Blender's main thread is single-threaded, but background tasks 
             (texture bake, render) run async on worker threads
Persistence: Blender's .blend file (native format), optionally with external assets
External Dependencies: Blender scene data, asset libraries (online or local),
                       Cycles/EEVEE rendering engines, external file system
Failure Tolerance: Idempotent operations (safe to retry), manual recovery on crash
```

## System 1 — Primary Operations (Blender Addon)

Autonomous addon command execution without unnecessary blocking.

**Includes:**
- mesh creation, subdivision, Boolean operations
- material assignment and property editing
- object transforms (translate, rotate, scale)
- modifier stacking and evaluation
- texture/image operations
- UV mapping
- armature/rigging
- particle systems
- animation keyframing
- viewport rendering / preview
- file I/O (import/export)
- tool panel interaction
- user modal dialogs (operator panels)

**Rule:**
Addon should complete user action without blocking on:
- Full viewport redraw (deferred, handled by Blender's event loop)
- Expensive file I/O (use async file operations or background jobs where available)
- Texture baking (must be non-blocking via Blender's job queue)
- Render preview (async, user can cancel)
- Asset library downloads (background fetch)

Critical synchronous checks remain:
- Validation before operation (is target object valid? does material exist?)
- undo/redo state machine (must be synchronous)
- scene data mutations (must be atomic from user perspective)

---

## System 2 — Coordination (Blender Addon)

Prevents races, duplication, and addon interference.

**Includes:**
- Undo/redo entry atomicity (one user action = exactly one undo entry)
- Modal state (prevent nested dialogs; one operator active at a time)
- Modifier stack ordering (prevent conflicting modifications applied twice)
- Material update deduplication (if operator runs twice, don't double-apply)
- Addon hook ordering (if multiple addons hook `frame_change_post`, what order?)
- Event queue coordination (is paint event processed before modifier evaluation?)
- Timer/callback sequencing (do background jobs serialize correctly?)
- Namespace isolation (addon A's operators don't collide with addon B's)
- Property write conflicts (two addons updating the same object property)
- Asset import deduplication (downloading same texture twice simultaneously)

**Primary question:**
> If a user action fires while an async operation (bake, render) is running, 
> or if two addons modify the same mesh simultaneously, does the system remain consistent?

---

## System 3 — Control & Authoritative State (Blender Addon)

**Includes:**
- Scene object hierarchy (Blender's native bpy.data structure)
- Addon-maintained state, if any (stored separately from Blender's, or in custom properties)
- Undo stack (as authoritative for operation reversibility)
- File serialization format (how addon data persists in .blend or external files)
- Dependency graph (mesh A depends on texture B which depends on file C)
- Modal/active state (which dialog is open? which tool is active?)
- Cache (processed/derived data, must remain consistent with source)
- External asset references (where are linked .blend files, textures, models?)

**Primary question:**
> If addon state diverges from Blender state (e.g., material is deleted but addon 
> still references it), how is the divergence detected and recovered?

---

## System 3* — Independent Audit (Blender Addon)

Verifies addon state against Blender reality and external evidence.

**Includes:**
- Scene consistency checker: orphaned object references, broken material links, missing textures
- Undo stack validation: can every undo entry replay without error?
- Asset reference audit: are all linked files, textures, models available on disk?
- Serialization round-trip: save → close → reopen → compare to original
- Viewport match: is displayed material the same as bpy.data state?
- Object hierarchy audit: no circular dependencies, all parents valid
- Memory consistency: no dangling pointers to deleted objects
- Modifier evaluation: does actual mesh match modifier parameters?

**Example audit logic:**
```
Internal addon state: material "Gold" assigned to object "Sphere"
Blender query: bpy.data.objects["Sphere"].active_material.name == "Gold" ✓
Undo replay: undo returns to pre-assignment state ✓
File round-trip: save → load → query still returns "Gold" ✓
Asset check: texture files referenced by material exist ✓
```

---

## System 4 — Intelligence (Blender Addon)

External sensing and adaptation; informs but does not block operations.

**Includes:**
- Performance monitoring: identify slow mesh operations, memory leaks, render time spikes
- User behavior tracking: which features most used, common error patterns
- Blender version compatibility: which newer APIs available? which deprecated?
- Asset library status: new downloads available? offline sources?
- GPU memory trends: are heavy operations approaching memory limits?
- Render time forecasting: if user requests 4K render, estimated time?
- Dependency updates: newer versions of linked .blend files available?
- Platform-specific guidance: macOS, Linux, Windows behavior differences

---

## System 5 — Policy & Emergency Control (Blender Addon)

Ultimate authority and emergency intervention.

**Includes:**
- Addon stability tier: alpha (experimental), beta (mostly working), stable (production-ready)
- Blender version requirements: min version 3.6, max 4.1 (if newer APIs break compatibility)
- Cancellation behavior: ESC key cancels operation cleanly, cleanup is guaranteed
- Data backup policy: before destructive operations (boolean, delete), confirm with user
- Conflict resolution policy: if addon A and B both modify same mesh, which takes precedence?
- Undo limit: max 100 undo entries (prevent unbounded memory growth)
- Permission model: certain operations require confirmation (overwrite file, delete hierarchy)
- Emergency disable: can addon be disabled if causing repeated crashes?
- Admin recovery: if addon leaves scene in broken state, can admin fix it?
- Audit logging: addon actions logged (for forensics if scene corrupts)

---

# 4a. Context Template: Creative / Editor Tool (desktop or WebGL)

Use this for a standalone editor: a 3D or CAD tool, a print-prep or slicer front end, an image,
audio or video editor, a diagram or design tool — in a browser (WebGL/WebGPU, workers) or on the
desktop (Electron, Qt, native).

## Audit Profile

```
Software Type: Interactive editor, single-user, document-centred
State Scope: The document or scene in memory, the undo stack, view state (camera, selection,
             tool mode), per-user preferences
Concurrency: One UI thread plus workers (geometry, generation, export), GPU uploads, async
             file I/O; a worker's result can land after the user has moved on
Persistence: The saved file (native format) and exports to other tools' formats; autosave
             and recovery files
External Dependencies: The file system, GPU / driver limits, independent producers and consumers
                       of its formats (slicers, other editors), optional cloud sync
Failure Tolerance: The user's work is never lost; every long operation can be cancelled
```

**Primary quantity:** the user's document — what the viewport shows, what the undo stack can
restore, and what the saved file reopens to. Observers (`browser-walks.md` §12): viewport,
outliner or inspector, undo stack, the saved file read back, any worker's copy.

**Systems in one line each.** **S1** commands and tools that edit the scene, generation and
export jobs. **S2** the command queue and undo stack, worker job ids and cancellation, the
ordering of worker results against newer edits (S23), file locks. **S3** settings and
preferences, tool modes, view modes and their automatic switches (S22: the user's toggle always
wins), units. **S3\*** the test suite and its fixtures, a save → reopen → compare round trip, a
format check against an independent producer and consumer (S24). **S4** imported files from
other tools, GPU capabilities, OS dialogs and permissions. **S5** autosave and crash recovery,
what happens on out-of-memory or a lost GPU context, confirmation before anything that
overwrites or deletes the user's work.

**Where defects live in this shape:** a worker's stale result applied over a newer edit; an undo
that restores the scene but not the derived data (supports, caches, GPU buffers); a gesture or
filter that works from the author's view only; a hit-test against a proxy instead of what the
user sees; a forced mode with a disabled toggle; a save that writes in place and loses the file
on a crash; an export proven only by our own importer.

**Final question for this shape:** if the viewport, the in-memory document, the undo stack,
background workers, GPU buffers and the file on disk disagree, does the tool know which is
authoritative, and can it save, undo and recover without losing the user's work?

---

# 5. Context Template: E-Commerce Platform

Use this when auditing a payment platform, marketplace, or order-fulfillment system. **This
template covers integrity only** — state, atomicity, idempotency, concurrency, persistence and
recovery as they apply to a shop, exactly as for any other system. Commerce doctrine (payment
settlement semantics, order lifecycle policy, inventory reservation, refunds, tax, promotions,
fulfilment, entitlements) belongs to `ecommerce-cia`; when this template matches, the report also
tells the user to run `/ecommerce-cia` (`SKILL.md` §0.3, §0.4).

## Audit Profile

```
Software Type: Web/distributed application
State Scope: Multi-user, cloud-backed
Concurrency: Distributed, high-volume simultaneous transactions
Persistence: Database (SQL/NoSQL), file storage, payment provider records
External Dependencies: Payment gateways, shipping providers, tax systems, 
                       invoice services, customer communication
Failure Tolerance: Idempotent payment processing, eventual consistency reconciliation
```

## System 1 — Primary Operations (E-Commerce)

- Storefront browsing and product search
- Shopping cart operations
- Checkout and payment initiation
- Order placement and confirmation
- Shipping selection and address entry
- Pickup location selection
- Free/promotional content acquisition
- Digital delivery
- Customer account management and order history
- Fulfillment initiation
- Invoice generation

**Rule:**
Do not block on analytics, non-critical emails, reporting dashboards, or marketing automation.
Critical: payment validation, inventory checks, fraud signals.

---

## System 2 — Coordination (E-Commerce)

- Transaction atomicity (payment + inventory update together or not at all)
- Coupon/promotion redemption limits (prevent over-redemption)
- Webhook deduplication (payment callback fires twice, don't charge twice)
- Inventory reservation and lock duration (prevent overselling)
- Idempotency on retries (customer retries payment, gateway processes it twice)
- Duplicate order prevention (same cart submitted twice)
- Refund atomicity (inventory restock + payment reversal + invoice adjustment)
- Tax calculation consistency (same result for same inputs)

**Primary question:**
> If customer clicks "Pay" twice, or payment gateway sends duplicate callback, or inventory 
> system is temporarily slow, can the platform guarantee exactly one charge and exactly one order?

---

## System 3 — Control & Authoritative State (E-Commerce)

- Order state (pending, paid, shipped, delivered, refunded, etc.)
- Payment state (authorizing, authorized, captured, failed, reversed)
- Inventory state (stock count, reservations, committed sales)
- Fulfillment state (picked, packed, in-transit, delivered)
- Customer data (address, preferences, order history)
- Ledger (financial transactions, credits, debits)
- Invoice state (drafted, issued, paid, disputed)
- Refund state (requested, approved, issued, settled)

---

## System 3* — Independent Audit (E-Commerce)

- Payment gateway reconciliation (did Stripe actually charge what we recorded?)
- Shipping provider reconciliation (did parcel actually ship?)
- Inventory audit (physical count vs. database count)
- Financial ledger audit (total credits = total debits)
- Invoice reconciliation (issued invoices vs. actual orders)
- Chargeback/dispute tracking (customer disputes vs. payments)
- Tax audit (collected tax vs. jurisdiction requirements)

---

# 6. Context Template: Workflow Orchestration (n8n, Zapier, etc.)

Use this when auditing automation workflows, node orchestration, or task scheduling.

## Audit Profile

```
Software Type: Workflow engine (API orchestration)
State Scope: Multi-user, stateless execution (state in external systems or execution logs)
Concurrency: Parallel execution of multiple workflows, each with sequential node steps
Persistence: Execution logs, error records, input/output archives
External Dependencies: APIs (dozens possible), databases, authentication providers
Failure Tolerance: Retry strategies, dead-letter queues, human-in-the-loop escalation
```

## System 1 — Primary Operations (Workflows)

- Workflow triggering (webhook, schedule, manual)
- Node execution (transform, filter, call API)
- Data passing between nodes
- Branching (conditional logic)
- Error handling (try/catch, fallbacks)
- Logging and output capture

---

## System 2 — Coordination (Workflows)

- Idempotency (same trigger fired twice shouldn't double-process)
- Webhook deduplication (Slack API sends webhook twice, only process once)
- Node retry logic (failed HTTP request retried, but not forever)
- Parallel execution safety (do branches interfere with each other?)
- Execution ordering (must Node A complete before Node B starts?)

---

## System 3 — Control (Workflows)

- Workflow definition (YAML/JSON representation)
- Execution state (in-progress, completed, failed, paused)
- Input/output archive (what did each node receive/return?)
- Credential storage (API keys, tokens)
- Variable scope (global vs. node-local)

---

**Reading receipt: _the profile picks the template, never the other way round_.** Quote this phrase on the report's receipts line (Step 6 in cia,
Step 7 in ecommerce-cia) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
