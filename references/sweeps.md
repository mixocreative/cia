# §0.9 Mandatory Sweeps — Cross-Boundary Invariant Violations a Green Suite Does Not Catch

Loaded by `cia` at Step 2, read in full, every run. Sweeps S1–S22 each end in one report line; a sweep with no line in the report was not done. Each sweep line names its sites, not a count: a path list (`path:line` or `path` per site) that the reader can open. `swept, 0 findings, 14 sites` is a claim; the fourteen paths are the evidence, and a line without them is the vacuous pass this skill exists to catch (S8), filed by the auditor. **Add one quoted line from one of those sites** — the predicate, the catch, the setting read, verbatim with its `path:line` — as proof the site was read and not merely listed by a grep.

Each item below is a real defect class that survived a green fast suite, a clean static analyser and a clean linter, and was found only by a second auditor reading the code by hand. Each sweep produces either a numbered finding or an explicit "swept, 0 findings, N sites inspected" line in the Step 6 report. No line means the sweep was not done.

## Step 0 — Map the codebase onto the Viable System Model before sweeping

The sweeps are not a grep list; they walk the channels of a VSM map of *this* codebase. Before S1 runs, produce and report a table with one row per module, directory, service, cron job, config surface and test suite:

| Component (path) | Primary VSM system | Channels (`producer → consumer`, with the system on each side) |
|---|---|---|

Systems: **1** primary operations (the code that does the work: checkout, order, fulfilment, request handlers); **2** coordination / anti-oscillation (locks, queues, idempotency keys, deadlines, ordering); **3** control (settings, feature flags, admin pages, config files, the values that tell System 1 what to do); **3\*** independent audit (test suites, verification scripts, reconciliation, probes); **4** intelligence / environment (vendor specs, external APIs, webhooks, callbacks, imports); **5** policy / identity / emergency (defaults, catch-block posture, kill switches, fail-closed rules). Report the map as line 2b / 3b of the Step 6 report: "VSM map: N components, M channels". Missing map = the sweeps had no site list and are not done.

Every sweep then enumerates its sites from the map's channels, and each defect class is a broken channel between two systems (column four of the taxonomy table below):

- every **System 3 → System 1** channel (a setting, flag, admin control or config value → the runtime code that must obey it) is a site for S5 and S6;
- every **System 1 → System 1 across time** handoff (value frozen at one step, read at a later step; SELECT then UPDATE) is a site for S1 and S2, and its missing System 2 coordinator is the finding;
- every **System 4 ↔ environment** boundary (vendor field, external payload, model output) is a site for S4 and S11;
- every **System 3\* → System 3** channel (what the suite or probe actually verifies about the control state) is a site for S7, S8 and S10;
- every **System 5 default** (catch block, fallback, absent kill switch) is a site for S3 and S12;
- every rename or refactor is a **System 1 ↔ System 1 binding** and a site for S9.
- every **design document, master plan, handoff note or migration** that names a component, table or control is a **System 3 → System 1 promise** and a site for S13;
- every audit whose scope is narrower than the map (one diff, one module) is a **System 3\* channel narrower than the system** and a site for S14;
- every object that crosses **customer → operator → fulfilment provider → payment provider** (an order, a shipment, a refund) is the site for S15, and it is the site that matters most: the four corners are four Systems 1/3/4 that each hold a partial truth about one thing.

A channel on the map with no sweep site named against it is unswept; say so in the report line rather than omitting it. The reverse also holds: a sweep whose site set on the map is empty — no hosted surface for S17, no scheduled detector for S20, no operator screen for S22 in a library or CLI — reports `no sites on the map` in one line, with the map row that proves it, and does not spend the run proving an absence twice.

## Taxonomy

**These are cross-boundary invariant violations (integration-level, emergent defects).** No single function is wrong; the defect lives in the relationship between two correct pieces, across time or across a layer. Code review sees functions and misses them by construction. Finding them requires behavioural tracing: follow one value from where it is written to every place it is later read, and follow one control from the admin screen or config file to the line of code that obeys it. Name the class in every finding:

| Term | Meaning | Sweep | VSM channel that is broken |
|---|---|---|---|
| **TOCTOU race** (time-of-check to time-of-use) | a predicate checked at one step and silently dropped at the step that acts | S2 | System 1 → System 1 across time, no System 2 coordinator |
| **Temporal coupling / stale snapshot** | a value frozen at one moment while a later reader re-reads live state | S1 | System 3 → System 1 read at two different times |
| **Semantic drift** | code's understanding of an external field diverges from the vendor's source of truth | S4 | System 4 ↔ environment (vendor) |
| **Dead control / broken control-to-consumer wiring** | an admin toggle, flag or setting that no runtime path reads | S5 | System 3 → System 1 command channel absent |
| **Fail-open default** | an error path that proceeds as if the failed read had succeeded | S3 | System 5 policy default missing or wrong |
| **Vacuous pass** | a suite that reports OK because the meaningful tests skipped or never ran | S7, S8 | System 3\* reading System 3's own conclusion |
| **Deferred-work residue** | a comment promising a follow-up that never landed | S6 | System 3 → System 1 channel promised, never built |
| **Rename residue** | a consumer still bound to the old name after a rename | S9 | System 1 ↔ System 1 binding broken |
| **Diagnosis without probe** | concluding a cause from an error message instead of a direct check | S10 | System 3\* without an independent channel |
| **Boundary schema drift** | a payload crossing a boundary is acted on before its shape and type are validated | S11 | System 4 ingress unvalidated |
| **Cascade / retry storm** | one step's failure or retry propagates as crash, duplicate write, or orphaned side effect | S12 | System 2 anti-oscillation absent, System 5 no circuit breaker |
| **Orphan capability / designed-but-unbuilt** | a class, table, column, admin control or design document that exists with no caller, no writer, no page and no gap-register row — capability promised, channel never built | S13 | System 3 capability with no System 1 consumer and no System 3\* register entry |
| **Scope shadow** | an audit run on one diff or subsystem whose report reads as whole-system green | S14 | System 3\* channel narrower than the map it reports on |
| **Corner disagreement / unreachable capability** | the customer, the operator, the fulfilment provider and the payment provider describe one object differently, or a built capability is not reachable under the shipped configuration | S15 | System 1 ↔ System 3 ↔ System 4, all four corners of one object |
| **Control with an off-system enforcement point** | a local setting claims to constrain a decision the user makes on a third party's surface, where the request cannot express the restriction and the provider's own back-office decides | S17 | System 3 control whose System 1 lies outside the map |
| **Sampled where it should have been enumerated** | a sweep reported clean from a sample; a finding later confirmed in that class proves the method rather than the instance was wrong | S18 | System 3\* measuring a subset and reporting on the whole |
| **Environment constraint never crossed** | a dependency's requirement on the host (fixed egress IP, persistent disk, cron granularity, inbound reachability) and the chosen host's capabilities are both documented, and nobody multiplied them — usually because the requirement was filed as a human checklist task | S19 | System 4 reading the environment, never compared with System 3's plan for it |
| **Service-variant confusion** | one provider's several variants of the same feature treated as one — different endpoints, templates, caps and fees — so a check that passed on one is filed as passing for all | S18 | System 4 read at brand resolution when the environment distinguishes services |
| **Blind instrument / dead watchdog** | a detector that examined nothing reports identically to one that examined everything and found nothing; or a scheduled check stopped running and nothing noticed | S20 | System 3\* with no liveness signal — the channel that reports on the others, unmonitored itself |
| **Unrendered / undesigned surface** | a state the system can reach has no screen, or one nobody has rendered, or one that cannot be dismissed by a person - so an exception is caught, logged, and decided by nobody | S22 | System 1 producing an event System 3 has no channel to see |
| **Vacuous or too-late proof** | a test asserting emptiness passes because the subject returns nothing for an unrelated reason; or the guard exists but sits so deep in a slow suite that nobody reaches it | S21 | System 3\* instrument that reports without measuring |

When the user asks for "code integrity", "audit", "review the wiring", "trace state across time", "every control to its consumer", or names any term above, the sweeps are the first thing that runs, before any function-level reading.

## S1 — Snapshot-vs-live reread (temporal coupling / stale snapshot)

For every value persisted at one moment (deadline, quota, reservation, computed price, cached permission, offered options), enumerate every later reader of the same concept and classify it as "reads the snapshot" or "re-reads live config". A later reader that re-reads live while an earlier writer froze a snapshot is a finding: the two disagree after any config change.

## S2 — Select-then-act predicate loss (TOCTOU race)

For every worker or batch that SELECTs candidates and mutates them one by one, the per-row UPDATE/DELETE must re-state the full selection predicate, not only the status column. A predicate checked at SELECT and dropped at UPDATE is a time-of-check/time-of-use finding.

## S3 — Catch-block failure posture (fail-open default)

For every `catch` on a critical path, write one line: what is caught, what happens next, fail-open or fail-closed. Fail-open on a configuration, permission, or feature-flag read is a finding unless an owner decision or ADR names that exact choice and its reason. **A secret derived from the environment's identity is a time bomb.** Any salt, key or token with a computed fallback — `hash(hostname)`, `hash(__DIR__)`, the container id, an ephemeral machine name — silently changes when the environment is rebuilt, and everything hashed against it stops verifying with no error anywhere. Check three things for each: production fails closed when it is unset rather than computing one; the value survives a container recreation; and every process that reads it (web, CLI tool, worker, test) computes the *same* one. A password written by a host-side CLI that cannot verify inside the container is this defect, and it reads as "wrong password" forever. Fail-open is not one posture: name the axis. On a **display or read path** (a listing, a search, a recommendation) fail-open to an empty or degraded result may be the right System 5 policy, provided the degradation is visible on a screen (S22) and counted by a detector (S20). On a **money, entitlement, permission, or configuration path** fail-open is a finding unless an owner decision or ADR names that exact choice and its reason. Grade the two axes separately, and say which one each `catch` sits on.

## S4 — External field semantics from the source document (semantic drift)

For every third-party field the code branches on (API status, webhook type, protocol sub-code), cite the vendor spec page or RFC section that defines it. A mapper comment is not evidence. If the spec distinguishes a family field from a subtype field, confirm the parser reads the one present in every case. No spec read → report line says "field semantics unverified". **Sample code is not a specification.** A vendor's runnable example proves the envelope it exercises and nothing else — it names no response fields, no status codes, no retry or acknowledgement rule. When the only vendor source on disk is a sample pack, the report says so and lists the manual that is missing; if the vendor publishes it, fetch it before writing a line against the boundary. A handoff note claiming "the sample folder is the complete authority" is an S4 finding, not a fact. **Gates must exist for every family that reaches them.** For every predicate a reducer, state machine or settlement path branches on (a status field, a close flag, a sub-code), list every input family that can arrive at that line and confirm the field is defined for each of them in the vendor document. A gate on a field that exists for one family only (a card-only close status read for a bank-transfer or pickup result) leaves the other families stuck in their prior state forever, with no error, no expiry and no alarm — the quietest money defect there is. **The vendor's recap is not the field table.** A manual's own summary list — a 注意事項 note, a changelog, a quick-reference — can omit a field the full request table defines (NDNF-1.2.5 p.40 lists every method flag except `TWQR`, which p.38 defines). Transcribe from the table and use the recap only as a cross-check; record any difference as a finding against the recap, not the table. **Same field name, per-family numbering.** A status field several families share may number its values differently per family (NDNF `CloseStatus` 3 = 請款完成 for cards and wallets but 請款失敗 for BNPL; the payment callback's integer `StoreType` numbers OK as 3 where the logistics `ShipType` numbers it 4). Keep one value table per family keyed on the family field, refuse a value that is not on its family's table, and never derive one document's code from another's integer.

## S5 — Control to consumer (dead control / control-to-consumer wiring)

For every admin toggle, feature flag, or settings row, grep for the runtime consumer in the user-facing path. A control with no consumer, or a consumer still reading the legacy source the control was meant to replace, is a finding. **The form is part of the control, and so is the queue.** When a gate is widened — a method that used to accept only one state now accepts two — every surface that leads to it must be widened in the same commit: the renderer that draws the button, the queue whose predicate lists the work, the filter on the desk. Widening the handler alone leaves a capability that exists, passes its unit test, and cannot be reached by the person it was built for (a dispatch control that accepted a cash-on-pickup order while the form that calls it still rendered only for `paid`). Sweep by predicate, not by method name: grep the old condition across renderers, queries and tests, and confirm each hit was considered. **The host's whitelist is a consumer.** When a module copies the request into a named field list before the controller sees it, every field the page posts and the list omits is a dead control that answers with a success notice (a `Turn ON` toggle whose `feature`/`enabled` fields were dropped by `stringsFrom()` for three weeks); a controller test that bypasses the host module proves nothing about it. Walk the whitelist against every `name=` the page renders, and treat a module that hands the request over another way as an exemption to be named, never as silence.

## S6 — Deferred-work comments are open gaps (deferred-work residue)

Grep critical roots for `TODO`, `FIXME`, `follow-up`, `until then`, `for now`, `temporary`, `pre-migration`. Each hit is closed with a cited commit or listed as an open gap.

## S7 — Skipped tests are unverified, never green (vacuous pass)

`Skipped: N` on DB-, network-, or browser-backed tests is reported as "N unverified". Confirm the backing service is up and env vars are exported in the runner's shell before running; a suite that skips because they are unset prints a meaningless `OK`.

## S8 — A written test is not a run test (vacuous pass)

Every test added or changed this session appears in the report with its exact command and the exact `Tests: N, Assertions: M` line from real execution against the real backing store. Expect first real runs of unrun tests to fail: they encode the author's assumption, not the system's behaviour.

## S9 — Rename residue

For every symbol, selector, template, route or config key renamed since the last audit, grep both sides in every consumer type (code, templates, styles, scripts, tests, docs). Parity guard tests stay red-visible; never whitelist to make the suite pass.

## S10 — Environment truth before diagnosis (diagnosis without probe)

Before concluding "not installed" / "data missing" / "blocked", run the cheapest direct probe (container list, TCP connect, health endpoint) and record it. An application error plus a port timeout is consistent with a stopped service; it is not evidence of lost data. Never provision, reset, or reinstall on an error message alone. **Framework and opcode caches mask the code you just changed.** Before concluding that an edit had no effect — a form that still does not render, a branch that never runs — clear the framework's compiled cache and restart the runtime, then re-probe. ProcessWire's FileCompiler, opcache, template caches and CDN layers all serve a previous version of a file that looks correct on disk. A diagnosis made over a stale cache sends the next hour into the wrong file.

## S11 — Boundary contract / schema drift

For every payload that crosses a boundary into this system (webhook, API response, message from a queue, import file, form post, structured output from a model), find where it is parsed and where it is first acted on. Between those points there must be explicit shape and type validation: required fields present, unexpected fields handled deliberately, numeric strings converted not trusted, null-for-collection refused, escape and encoding handling defined. A parser that hands a raw decoded structure straight to logic is a finding. Name the boundary as `producer → consumer`. **Vendor limits are asserted where the value is sent, not where it is displayed.** A cap the vendor enforces (amount, count per call, length, character set) that the code checks only in the UI layer is unvalidated at the boundary: the request that crosses it fails, or the vendor silently omits the option, after the user has committed. Re-assert every vendor cap on the server against the exact value that will be sent.

## S12 — Cascade, partial failure and retry storm

For every outbound call and every inbound retry source, answer: what happens on half-way failure, timeout, or late success after the caller gave up? Per-step timeout? Bounded retry with backoff, on an idempotent action only? Circuit breaker or degrade path instead of crash or unbounded loop? A retry that repeats a non-idempotent write, or a failure that leaves an earlier step's side effect orphaned, is a finding. Trace the chain and state which downstream effect the upstream failure produces. **A wait with no ceiling is a leak.** Any state that waits for an external signal the environment cannot guarantee (a callback the sandbox cannot emit, a push with no documented retry) must have a ceiling that routes to a human queue — never an automatic reversal — and a sweep that lists what is waiting. State the ceiling and the queue; "the callback will come" is not a design. **A browser-returned result is not a server channel.** Vendors often deliver a result twice: once to the user's browser (a return URL, a "customer URL" form post) and once server-to-server (a notify URL), and the two carry different fields and fire at different moments. Anything the system needs before the user's next action — a consignment number, a store, an instruction — must have a server-side path (the notify channel or a poll of the vendor's query API); a design that takes it only from the browser post loses it the moment the tab closes.

## S13 — Orphan capability / designed-but-unbuilt

Three greps, one table. (a) For every class under the admin, control, settings or catalogue roots, grep for a caller outside its own file and its tests; a control class with no page, controller or module that renders it is an orphan. (b) For every table column and enum added by a migration, grep for a writer in runtime code (not only a test); a column nobody writes is scaffolding, and scaffolding that a later reader treats as data is a finding. **Grep the identifier alone and read every hit — never the identifier plus an SQL keyword on the same line.** A column written by a multi-line `UPDATE … SET` whose `SET` sits six lines above the column name is invisible to `grep 'col.*SET'`, and most non-trivial SQL is multi-line. One pass reported a live column as having no writer anywhere and was one sentence from filing it as an orphan with five consumers treating it as scaffolding. **A false orphan costs exactly what a missed one does**, because it sends the next session to rebuild something that already works — so confirm an absence by reading the hits, not by trusting a narrower pattern that returned none. (c) For every design document, master plan or handoff note under `docs/` that names a component, check that the component exists on disk **or** that the gap register carries one row naming it as unbuilt with its blocker. Report each orphan with its three states — designed / coded / wired — and say which owner-side blocker, if any, stops it. A capability that is designed and coded but not wired, and whose absence the register does not record, is the most expensive shape of gap: it looks done from every direction except the customer's.

## S14 — Scope shadow

State the scope of this run in the first line of the report: whole system, one subsystem, or one diff. When it is narrower than the VSM map, list the System 1 domains on the map that were **not** walked this run and the date of the last run that did walk them (from the handoff or the register). A narrow-scope report that omits this list reads as whole-system green and is itself a finding against the audit. Never let "0 findings" stand without the scope beside it.

### S14.1 — The plan is a scope claim, and an unmarked plan is a false one

S14 above governs the *audit's* scope. The same failure lives one level up, in the document the
team steers by, and it is more expensive because that document is trusted without being re-read.

Three rules, each from a plan that was believed while being wrong:

1. **Enumerate tracks, not phases.** A launch plan ran six phases covering correctness and deploy,
   and silently omitted two whole tracks — the content and data migration, and the design work that
   *gated every test in phase four*. Neither is code, so neither appeared in a plan written by
   reading code. **Ask what has to be true for this to be finished that no file in the repository
   would ever mention**: migrations of content, third-party account states, physical or manual
   steps, someone else's sign-off. A plan missing a track is worse than no plan, because it is
   trusted.
2. **Every item carries a mark, and there are only three.** Done, open, or waiting-on-someone-named
   — with the evidence for *done* and the blocked-thing for *waiting*. Unmarked items are read as
   done by whoever skims it next. "Nearly finished", "mostly works" and an item with no test and no
   citation are all **open**.
3. **A dated external wait is not a task.** When progress genuinely depends on another party,
   record who was asked, when, what it blocks, and where the answer will land. An unrecorded wait
   is indistinguishable from work nobody did, and it is the item that will be discovered last.

And the drift check, which costs one pass: **a prerequisite outlives the decision that created it.**
One plan required assets to be pruned before work could start; a later decision forbade deleting
those assets outright. Both sentences were live, in different files, and the older one was still
gating work. **When a decision reverses an assumption, grep the plans for the gate it created** —
the reversal is recorded where the decision was made, never where the gate sits.

## S15 — The four-corner end-to-end walk. THE HIGHEST-VALUE DATA IN THE SYSTEM IS THE DATA THAT CROSSES ALL FOUR CORNERS

For a system that moves money or goods, the four corners are **the customer surface**, **the operator / admin surface**, **the fulfilment or logistics provider**, and **the payment provider**, with the database as the fifth point that all four claim to describe. Every other sweep looks at one channel; this one walks one *object* — an order, a booking, a shipment, a subscription period — through every corner it touches, in sequence, and asks at each state: **can all four corners answer what is true right now, and do their answers agree?** A state where one corner cannot answer, or answers differently, is a finding even when every function on the path is correct.

Method, per money-or-goods flow (do not summarise this from the code's docblocks; trace it):

1. **List the states** the object can occupy, from first click to terminal (paid / delivered / refunded / cancelled / returned).
2. **For each state, fill four cells**: what the customer sees, what the operator sees and can *do*, what the fulfilment provider believes, what the payment provider believes. Cite file:line for the first two, the vendor field or callback for the last two.
3. **Mark the disagreements.** A customer page that says "pay at the counter" while the parcel is already collected; an operator queue that filters on a status the object no longer has; a provider that has moved on while the local row has not. Each is a finding with the class named (usually stale snapshot, dead control, or status-symmetry gap).
4. **Mark the unanswerables.** A state where the operator has no control, no queue row and no instruction is a finding: the system can enter a state a human cannot leave.
5. **Mark the reachability.** Walk the flow against the configuration production will actually run (the seed, the migration defaults, the flags as shipped) rather than a test fixture. A feature that is built, tested and unreachable under the shipped configuration is **CRITICAL** and is reported as such: every document says it is done and no customer can use it.
6. **Name the settlement evidence.** For every state that claims money moved, say which artefact proves it (a verified callback, a reconciliation query, an operator-recorded reference) and confirm no other signal is allowed to set it.

**Test consequence — this changes what a test is allowed to be.** Every test written for a flow that crosses corners must say which corners it covers, and the suite must hold at least one test per money path that walks **all four**, end to end, with the provider side faked at its own boundary (a signed callback body, a provider query response) rather than by calling the local method that would have handled it. A suite made only of single-corner tests can be entirely green while the corners disagree — that is the exact shape this sweep exists to catch. When the project ships an end-to-end walk harness (headless scripts, browser walks, a scenario matrix), its coverage and its *unwritten* scenarios are part of this sweep's report line, not a separate concern.

**The environment must be able to render what the sweep claims to have walked.** Before reporting a four-corner walk as done, confirm the running system can actually reach each corner: the pages exist (a catalogue with no page rows makes every product URL a 404 and no walk of the customer corner is possible), the operator can sign in, the provider sandbox answers. Seed gaps are findings of this sweep, not excuses for skipping it — they block the owner's own sign-off as surely as a bug, and they are usually one seeder run from fixed. Walk the corners in the running app, not only in the suite: a test renders a class in isolation, a browser renders what the operator will actually see.

Report line format: `S15 — walked N flows × M states; four-corner table in the report; K disagreements, J unanswerable states, R reachability findings.`

## S16 — Terminal-state accountability. EVERY FLOW MUST END SOMEWHERE A PERSON CAN ACCOUNT FOR

Where S15 asks whether the corners *agree*, this asks whether the object ever *ends*, and whether anyone is told when it ends badly. The owner's instruction, which is really an audit rule: *"No delivery or transaction should allow go dead quietly with loose ends, all ends must be tied and traceable"*, and *"anything system cannot handle must hv badge or flag in admin panel of order management page to let admin handle and notice."*

The defect this catches is not a wrong value. It is an object that stops moving and nobody finds out: the one class where **every function on the path is correct, every test passes, and the loss is real**. It hides from S1–S15 because there is nothing to disagree with â there is simply no further event.

Method, per flow that moves money or goods:

1. **Enumerate the terminal states, then enumerate the non-terminal ones.** Any state an object can occupy that is neither terminal nor guaranteed to advance is a candidate finding. For each, name the thing that advances it: a callback, a worker, a clock, a human. "It will arrive" is not an answer; name the code.
2. **Kill each advancer in turn and ask what happens.** The callback never arrives. The worker is not scheduled, or throws on its third item and stops. The provider answers once and never again. The human never looks. For each: does the object eventually reach a state someone can act on, or does it sit? An object that sits forever is a **silent death** and is HIGH at least.
3. **Follow every swallowed signal.** A `catch` that logs and returns, a queue row marked done on a failed send, a `return false` a caller ignores, a retry budget that simply runs out. Each is a place where the system decided something and told nobody. Ask where the *last* copy of that fact lives, and whether anything reads it.
4. **Check both halves of a two-fact truth.** Where a state claims two things happened — the goods moved *and* the money arrived, the file was delivered *and* the entitlement was granted — confirm they are two records that can disagree, and that a disagreement raises something. A system that infers the second from the first cannot detect the case where only one is true.
5. **Then check the notice lands on a working surface.** This is the half that is usually missing. An alert row nobody queries, a log line, an email to an address nobody reads, a table with no page — none of these is a notice. The test is: **is there a screen the operator already opens every day on which this thing becomes visible?** For a shop that is the order list and the order page; for another system, name the equivalent. A capability to handle the exception, on a page nobody opens, is a dead control (S6) wearing a different hat.
6. **Report the unattended set.** Every state where the object can stop with no advancer and no notice, as a table: state, what should have advanced it, what the operator would see, how they would ever find out. An empty table is a real result; an absent table means the sweep was not run.

**Grading.** Money or goods that can be lost with no signal: **CRITICAL**. An object that can sit forever but is recoverable once noticed: **HIGH**. A notice that exists but only in a log or a table with no screen: **HIGH** — by the owner's rule that is not a notice at all. A notice on a screen nobody has a reason to open: **MEDIUM**.

Report line format: `S16 — N flows × M non-terminal states; K silent deaths, J notices that reach no screen; unattended-state table in the report.`

### S16.1 — Every non-terminal state deserves a queue, and the queue is where the bulk action lives

S16 asks whether a state has a **badge**. The badge is the minimum and the **queue** is the useful
form: an operator opens *"what needs doing next"*, not *"records, filtered by status"*. The rules
below came out of designing one operator desk and apply to every desk.

**Check, per non-terminal state:** is there a queue that lists the items sitting in it, and does that
queue carry the action that moves them on? A state whose only surface is a per-record badge makes the
operator hunt for the records one at a time, and **a worker that already computes the list and writes
it to a log or an exit code is the queue's missing half**.

**Four rules that generalise past any one desk, each earned from a trap:**

1. **The single action is a batch of one.** Two code paths drift, and the one that drifts is the one
   without the precondition. Write the batch; let the single case call it with a selection of one.
2. **Carry the precondition in the `WHERE`, always.** `UPDATE … WHERE id = ? AND <what made this row
   eligible>`, then read the affected-row count. Closes the select-then-commit race, makes double
   clicks harmless, needs no lock and no version column. **Never `UPDATE … WHERE id = ?` alone** —
   in a desk or anywhere else.
**2a. A state transition and a value edit need different preconditions, and conflating them is a silent data loss.** Rule 2 above is not one rule but two, and the second is the one that gets missed:

| | Precondition | Why it is enough, or is not |
|---|---|---|
| **State transition** — mark dispatched, mark paid, cancel | `WHERE id = ? AND dispatched_at IS NULL` | **Self-protecting.** The condition can only be true once, so the second writer matches zero rows and learns it lost. The row count *is* the answer |
| **Value edit** — price, stock, a note, a cost | `WHERE id = ?` | **Not enough, and it fails silently.** There is no natural once-only condition on a value. Two operators editing the same price both match, both succeed, and the first edit vanishes with nobody told |

**For a value edit, carry the value you read**: `WHERE id = ? AND price = ?` — compare-and-swap — or
a `version` / `updated_at` token if several fields move together. A zero row count then means
*"somebody changed this while you were looking at it"*, which is a sentence the operator can act on,
and **the alternative is not a conflict, it is a disappearance.**

This matters most in exactly the place it is least expected: a **bulk editor** feels like typing in a
spreadsheet, so nobody thinks about concurrency — and it is the surface where one operator can
silently discard fifty of another's edits in a single click.

**2c. `rowCount()` may mean *matched*, not *changed* — check the connection before trusting the number.** MySQL's default reports rows the `SET` actually changed; with `PDO::MYSQL_ATTR_FOUND_ROWS` it reports rows the `WHERE` matched, and a codebase may enable that deliberately — one did, to stop idempotent re-saves reading as *"not there"* (`fb64069e`). Rules 2 and 2a survive either setting **only because the precondition is in the `WHERE`**: a row that no longer qualifies is not matched, so it is not counted, whichever semantic is on. What does *not* survive is any code reading `rowCount() === 0` as *"nothing changed"* — under `FOUND_ROWS` a no-op re-save matches and reports 1. A test asserting the old semantic was found red, unreached, at about test 4700 of a six-hour suite. **Grep the connection for `FOUND_ROWS` before writing or auditing any row-count logic, and if the contract needs "nothing to change" to read as zero, put that in the `WHERE` too** — NULL-safely, with `<=>`, because the columns compared are usually the ones that start NULL.

**2b. Validate per cell, not per submission.** One bad value must not reject the other forty-nine.
Same rule as showing ineligible rows with their reason: the batch reports per row, and the rows that
were fine are saved.

3. **If two rows could legitimately differ, it cannot be a header field.** One shared field for a
   per-item value writes the same tracking number, refund amount or invoice number onto every row in
   the selection. The test is one sentence: *could two selected rows honestly want different values?*
4. **Ineligible is explained, never silently dropped and never blocked.** Show the excluded rows with
   their reason. **Generalised to every disabled control in the product**: a greyed button says why it
   is grey — an S22 surface kind of its own, and the cheapest operator-experience win in most
   codebases.

**And the one that is about people rather than rows:** an operator action that can reach a customer
gets a **"tell them" checkbox, defaulted on, with the unchecking recorded — who and when.** A
customer who was never told must be distinguishable from one somebody decided not to tell. The
checkbox writes *intent*; the sending stays with whatever durable sweep already sends, because a
send-inside-the-click makes the customer's message depend on the operator's browser staying open.

## S17 — Controls whose enforcement point is outside the system. A SETTING THAT CANNOT REACH THE PLACE THE DECISION IS MADE IS A LABEL, NOT A CONTROL

The owner's question that defines this sweep: *"How do we restrict user use which chain by toggle? Or do we trust our toggle auto reflects payment gateway setting?"*

S6 asks whether a control reaches a consumer. S13 asks whether a capability has a caller. **Both search this codebase, and both pass when the consumer is somebody else's software.** That is the hole. The shop had a per-carrier admin toggle, stored in its own table, read by its own storefront, with tests. The customer chose their carrier on a page the *payment gateway* rendered, from a list the gateway's own back-office controlled, and the request field the shop sends has no parameter that can express the restriction at all. Every local check was green. The toggle governed nothing.

The signature: **a decision that happens on a third party's surface — a hosted checkout, a hosted picker, an OAuth consent screen, a courier's booking page, an app-store purchase flow — while a setting on our side claims to shape it.**

Method:

1. **List every decision the user makes outside your UI.** Hosted payment pages, store or locker pickers, carrier selection, consent screens, plan choosers, anything reached by a redirect or an embedded widget. For each, name the redirect or handoff in your code — that call is the entire surface you control.
2. **For each such decision, find the local setting that claims to constrain it.** An admin toggle, a feature flag, a catalogue of options, a config file. If none exists, the decision is simply theirs and that is fine — say so and move on. If one does exist, it is a claim, and the next two steps test it.
3. **Open the provider's specification for the request you actually send, and find the field.** Not their marketing page, not a blog, not your own wrapper's docblock — the request-field table in the integration manual, by page. Ask one question: **can this request express the restriction the setting claims?** Quote the field, its permitted values and its defaulting rule into the finding. Very often the answer is that the field has two coarse values where your setting has six fine ones.
4. **Find where the provider says the real decision lives.** Manuals usually state it plainly in a sentence nobody reads — a merchant back-office setting, an account-level activation, a per-sub-type approval. Whatever it names is the actual enforcement point, and it is outside your repository and outside your tests.
5. **Then decide which of three shapes the system is in**, and say which in the report: **(a) enforceable** — the request can carry the restriction, so wire the setting to the field and test it; **(b) not enforceable, and the setting is a lie** — either delete it or redefine it as "what we accept", which then requires a rule for what happens when the provider returns something outside the set (S16 applies: a badge, not a silent accept); **(c) enforced by the provider's back-office** — the setting must be documented as a mirror of a console value, with the console step in the deploy prerequisites, and something must reconcile the two or they will drift silently.
6. **Check the return path for values your local set does not contain.** Whatever the provider's surface offers, it will one day return an option your configuration says is off. Find the code that receives it. If it accepts it silently, that is the finding — the toggle is not merely inert, it is now producing state the operator believes cannot exist.

**Grading.** A setting that constrains money, carrier or fulfilment and provably cannot reach the decision: **HIGH** — it is a control the operator will make decisions with. Silent acceptance of an out-of-set value returned by the provider: **HIGH**. A mirror-of-console setting with no reconciliation and no deploy step: **MEDIUM**, raised to HIGH once two operators can edit either side. A cosmetic setting correctly documented as cosmetic: not a finding.

**The reading rule this sweep exists to enforce:** when a provider's manual is on disk, *read the field table for every field you send*. A wrapper's docblock describing what a field does is your own summary of their document and carries none of its authority — several of the defects this sweep was written from were wrong summaries written confidently by the same people who later audited them.

Report line format: `S17 — N off-system decision points; K settings tested against the provider's field table; findings by shape (enforceable / lie / console-mirror).`

## S18 — Exhaustive enumeration against the authority document. A SPOT CHECK THAT FINDS A HOLE HAS DISPROVED THE METHOD, NOT JUST THE ANSWER

In the owner's words: *"One hole of that shape means the method that found it was wrong, not just the answer — so the fix is to walk every combination against the manuals rather than spot-check."*

This is the sweep that makes the other seventeen honest. Every one of them can be run on a sample and reported as clean, and a sample is exactly what produced the defect this was written from: an auditor read the code for one delivery method, found the control, and wrote "the per-method toggle exists" into a plan. There were four methods, two gateways and a vendor manual on disk, and the claim was false for all of them.

**Two rules, and the first one is the one people skip.**

**Rule 1 — a confirmed finding invalidates the sweep that missed it.** When a finding is confirmed in some class — one control that does not reach its enforcement point, one state with no notice, one field misread from a manual — do not fix the instance and move on. **Re-run that sweep exhaustively across its whole domain**, every member, and report the count you walked. The instance was found by luck or by a user; the rest of the class is still there. A report that fixes one and says nothing about the other eleven is the same failure one iteration later.

**Rule 2 — enumerate the combinations, and cite the authority per cell.**

1. **Name the authority for the subject.** The vendor's integration manual, the RFC, the schema specification, the regulator's text, the hardware datasheet. **If a copy is on disk, that copy is the authority** and your own wrapper's docblocks are not — they are a summary somebody wrote, often the same person now auditing them.
2. **Enumerate the dimensions the shipped configuration can actually produce**, not the theoretical Cartesian: which options are enabled, which states are reachable, which environments ship. Write the grid down before checking any cell, because a grid built while checking is a grid that omits what was not checked.
3. **Walk every cell.** For each, the question is the same: what does this system send or assume, what does the authority say, and do they agree? Record the answer **with its citation — page, section or field name.**
4. **A cell with no citation is `UNVERIFIED`, never `OK`.** This is the rule that does the work. An unverified cell is a reportable state, and a matrix of thirty cells with nine unverified is a far more useful result than a sentence saying the integration looks fine.
5. **Report the matrix itself**, not a summary of it. The reader must be able to see which cell was checked against what.

**Grading.** A cell that contradicts the authority: graded on its own consequence. A class re-walked after a confirmed finding, turning up more of the same: each on its own consequence, and the original finding is raised one level because it was systemic rather than isolated. A matrix with unverified cells: not a finding in itself — but reporting it as clean is.

### S18.1 — The manual is not the only authority, and often not the best one

Three failures that only appear when a provider's tooling is actually *used*, none of them
visible in the manual that had already been read:

1. **The vendor's own validator knows rules the vendor never documented.** An import wizard
   rejected a row with 「姓名不可超過五個中文字」 — a five-character cap on a name field, stated in
   no manual, no FAQ and no field table, and one that silently decides which of our customers can
   use the feature at all. **Where a provider offers a validator, a sandbox, a preview step or a
   dry run, run it and read its refusals.** Its error messages are a specification you cannot get
   any other way, and they cost one afternoon rather than one incident.

2. **The artefact the provider produces outranks the documentation about it.** A printed label
   said the payment deadline was four days; the FAQ said seven. The label is what the counter
   obeys. **Rank authorities explicitly: the thing the system emits (label, receipt, callback
   payload, generated file) > the integration manual > the help centre > our own docblock.** When
   two disagree, the lower one is not a second opinion, it is a stale copy.

3. **One provider is several services, and they are not interchangeable.** The same vendor offered
   three variants of one feature, each with its own page, its own upload template, its own caps and
   its own fee table — and the correct file on the wrong variant's page failed with a generic
   format error that suggested nothing of the kind. **Enumerate variants, not providers.** Each
   variant is its own row of this matrix, carrying its own limits, its own endpoint or page, and
   its own money.

4. **A citation that does not resolve is not a citation.** A page number from a PDF reader, the
   folio printed in a footer, and a section number in a table of contents are three different
   coordinates for the same paper, and vendor manuals routinely print a folio exactly one lower
   than the PDF page. An audit whose whole method is *"a cell with no citation is UNVERIFIED"*
   collapses the moment its own citations land on the wrong page: the next reader opens it, finds
   something else there, and either re-derives the finding from scratch or quietly stops trusting
   the register. **Say which coordinate system you are using, once, in the document. Verify every
   citation by extracting that page and grepping it for the thing you claimed is on it. Prefer the
   page where the several facts you are leaning on appear together** over the first page that
   mentions any of them.

   **And extract tables with the layout preserved** — `pdftotext -layout`, or whatever your
   tool's equivalent is. Without it a two-column code/message table collapses into two
   run-on paragraphs whose rows no longer line up, and the limit you are trying to cite
   binds to the wrong code or to nothing at all. A table read without it is a table you
   have not read, and the `UNVERIFIED` it produces is an artefact of your tooling rather
   than a fact about the document.
   **And when `-layout` and the raw extract disagree, the raw one preserves row order — read both.**
   `-layout` keeps columns but can shift a cell one row on a multi-line table; the raw extract
   loses columns but never reorders rows. A column-shifted `-layout` read once put a 4-hour lockout
   sentence beside the wrong error code and was one step from "correcting" a code that was already
   right in shipped software. For any code-to-meaning binding you are about to act on, confirm it
   in the raw extract — or, best, find the vendor's own prose that names both together, which a
   manual's FAQ usually does.
   **And count a table by its cells, never by a column read.** A `-layout` count of one column
   once said 79 codes; the PDF's own ruling lines (`pymupdf` `find_tables`, or any extractor
   that reads cell borders) said 125, because a fifth of the table was a second code column
   the first read never saw. Extract cells, count rows, then cross-check the raw order.

Three rules that fall out, and all three belong to every S18 run:

- **A list you display is a promise.** When a picker, dropdown or option set is fed from a
  provider's directory, filter it by *the capability being offered*, not by existence. The
  directory listed branches that do not offer the service in question; offering one is a failure
  that happens to a person standing at a counter, not to a log file.
- **When the authority contradicts itself, surface both and decide with the owner.** The same page
  capped one value at 1,000 in one section and 10,000 in another. Recording the convenient number,
  averaging them, or picking the one that makes the feature work is how a documented limit becomes
  an undocumented incident. Contradiction is a finding with a citation on each side.

- **A wrong citation re-walks the citations, exactly as a confirmed finding re-walks its class.**
  The rule is not suspended for the audit's own output. One page number found to be a folio means
  every page number written in the same sitting was probably a folio; re-extract all of them,
  correct the ones that moved, and say in the document that you did — including in any patch not
  yet applied, so the docblock that eventually ships names a page that exists.

Report line format: `S18 — subject, authority cited; N cells enumerated, M verified against the document, U unverified; matrix in the report. Re-walks triggered by findings this run: K.`

## S19 — Environment-constraint reconciliation. A REQUIREMENT THE HOST MUST SATISFY, NEVER CHECKED AGAINST THE HOST THAT WAS CHOSEN

The owner's question: *"does [this] also need whitelist IP…? If so our shared hosting launch won't make it."* Both facts were already written down. **In the same document.** The provider's requirement was in the deploy prerequisites; the chosen host was in the section above it. Nobody multiplied them.

This is not S17 (a control whose enforcement is elsewhere) and not S18 (sampling where enumeration was needed). It is narrower and more embarrassing: **two known facts, never crossed.**

**The mechanism that hides it, and it is worth stating because it is almost universal:** the requirement had been written as *a task for a human*. "Register the outbound IP with the provider" became a tidy row in a deploy checklist — and **the moment a requirement becomes a checklist item, it leaves the audit's scope.** Nobody asks whether the task is *possible* on the target; they only track whether it is *done*. A constraint converted into a chore is a constraint nobody validates.

Method:

1. **Extract every environment precondition your dependencies impose.** Read them out of the integration manuals, not out of your own notes: a fixed or allowlisted egress IP, a static hostname, an inbound webhook reachable from the public internet, a minimum TLS version, a specific cipher or certificate chain, a runtime extension, sub-minute cron, long-running or background processes, persistent local filesystem, outbound ports other than 443, a clock within N seconds of theirs, a fixed timezone. **Cite each to its page**, exactly as S18 requires.
2. **Write down what the target environment actually provides.** Not the environment you develop on — the one the thing ships to, named: this host, this plan, this tier. Shared hosting, a container platform that rotates egress, a serverless runtime with no persistent disk, a PaaS that recycles processes, a corporate network with an outbound proxy.
3. **Cross them. Every requirement against every environment the system is deployed to.** One row per pair. Three verdicts: **satisfied** (say how it is known, not assumed), **not satisfied** (a finding, graded on what stops working), **unknown** (a question for the host, and a finding until answered).
4. **Grade an unknown as a finding, not as a gap in the report.** "The host may or may not have a stable egress IP" is the state in which a launch is planned around a capability nobody confirmed.
5. **Say what breaks, in the system's own terms.** Not "IP allowlisting may be required" but "parcels cannot be booked, and the failure is a refusal from the provider that our code currently logs and does not badge". The consequence is what gets a decision made; the requirement alone gets filed.
6. **Re-check on every environment change.** A host migration, a plan upgrade, a move from VM to container, a new region — each invalidates this sweep's result entirely, because every row was about an environment that no longer exists.

**Feed the answer back into S18.** The deployment environment is a dimension of that matrix, not a footnote to it: **a cell verified against the manual, on a host that cannot satisfy the manual's precondition, is a verified cell about nothing.**

**Grading.** A requirement the target provably cannot satisfy, on a path that moves money or goods: **CRITICAL**. One the target probably cannot satisfy, or can satisfy only unreliably — a shared egress IP that may rotate: **HIGH**, because the failure is intermittent and intermittent failures are the ones nobody reproduces. An unknown on a money path: **HIGH** until answered. A requirement satisfied but undocumented, so the next host move loses it: **MEDIUM**.

**And the rule this sweep leaves behind:** when an audit hands a requirement to a person as a task, it must also record *what makes the task possible* and check that. Otherwise the checklist is complete on a host where the box cannot be ticked.

Report line format: `S19 — R environment requirements extracted and cited; E environments crossed; satisfied/not-satisfied/unknown = A/B/C; table in the report.`

## S20 — Liveness of the safety net itself. ZERO FINDINGS AND ZERO LOOKING ARE THE SAME REPORT UNLESS SOMEBODY DESIGNED THEM APART

The First Law — *"Nothing should die silently!!"* — applied to the watchdogs themselves.

S16 asks whether an **object** can stop moving unnoticed. **S20 asks it of the detectors**: the audits, reconcilers, monitors, sweeps, alarms, scheduled jobs and health checks — everything whose whole purpose is to notice. They are the last things anybody thinks to watch, and their failure is uniquely quiet, because **a check that examined nothing produces exactly the output of a check that examined everything and found nothing**: no findings, no error, a tidy summary line, exit 0.

The three that actually happen, all three confirmed in one codebase:

1. **The check ran and verified nothing.** A settlement audit asked two gateways about every order and every answer was "unreachable". It counted the unknowns, raised nothing, exited 0. The likely cause — an outbound IP the provider had stopped accepting — would have left the shop back on a single unverified callback per order, *with nothing saying the second witness had stopped*.
2. **The check stopped running at all.** A heartbeat was written by every worker and read by nobody. A crontab lost in a host migration, a dispatcher throwing on its first line, a flag switched off and forgotten — each is silent, because nothing runs to produce the error.
3. **The check ran, found something, and told a table.** Covered by S16 step 5, and it belongs here too: an alarm with no screen is a detector whose output dies where it lands.

Method — apply to **every** component whose job is to notice:

1. **Enumerate the detectors.** Scheduled jobs, reconcilers, audits, validators, health checks, alarm writers, retry sweepers, watchdog timers. If you cannot list them, that is the first finding.
2. **For each, separate "ran" from "worked".** Demand two numbers, not one: **coverage** (how many things were actually inspected) and **findings** (how many were wrong). A report carrying only findings cannot distinguish a clean system from a blind instrument. Where coverage can be zero while the run still "succeeds", that state must be named and raised — *blind*, *degraded*, *nothing verified* — never folded into success.
3. **Give every scheduled thing a heartbeat, and make something read it.** Writing a heartbeat nobody queries is theatre. Something must compare last-run against expected-interval and escalate the gap — with a grace of a few intervals so one late run is not an alarm, and with *never ran* treated as the loudest case rather than the quietest, because on a fresh deploy it means the schedule was never installed.
4. **Walk the escalation to a surface a human opens.** For each detector: where does its output appear, and who opens that? A log, a table, an email to an unread address and an exit code nobody reads are all the same answer — nowhere.
5. **Then ask the recursive question, and answer it once rather than forever.** Who watches the watcher? The regress terminates only by leaving the system: an exit code a scheduler mails, an external uptime probe, a dead-man's switch a third party trips when a ping stops arriving. **Name the outermost check and confirm it is outside the process it watches.** A monitor inside the thing it monitors shares its failures.
6. **Test the blind case explicitly.** A detector's test suite must contain "it examined nothing and said so". That test is almost never written, because it feels like testing the absence of work — it is testing the difference between silence and safety.

**Grading.** A detector on a money or safety path that cannot distinguish blind from clean: **HIGH** — every run it makes is uninterpretable, including the ones already filed as green. A scheduled money-critical job with no liveness signal: **HIGH**. A detector whose output reaches no human surface: **HIGH** (S16 rule six). No outermost check outside the system: **MEDIUM**, and it is the one to state plainly rather than grade, because it is an architectural choice the owner should make knowingly.

**The sentence to carry out of this sweep:** *a green report from an instrument nobody has proved is looking is not evidence of health — it is evidence of a report.*

Report line format: `S20 — D detectors enumerated; C report coverage separately from findings; H have a liveness signal something reads; E escalate to a human surface; outermost check: <named, or NONE>.`

## S21 — The suite is an instrument too. A PASSING ASSERTION THAT SOMETHING IS EMPTY PROVES NOTHING UNTIL SOMETHING PROVES IT CAN BE NON-EMPTY

S20 asks whether the detectors are looking. **S21 asks it of the test suite**, which is the detector everything else is trusted on. Five shapes, the first four confirmed in one codebase in one day:

1. **The vacuous pass.** A query used by four tests returned nothing at all, because of a defect none of them was about. The two tests asserting *"and the result is empty"* passed — that is what they asked for — and the two asserting a result failed. The failures looked like a test problem precisely because their siblings were green. **Whenever the subject of a test is a query, a filter, a collection or a sweep, at least one test must prove it can return something, under the same conditions.** And watch the **assertion count**, not only the colour: if fixing a bug makes assertions go *up*, assertions were not being reached, and every earlier green run was reporting on code it never executed.
2. **The runner is one environment.** A test that loads real configuration into the runner's own process — a framework bootstrap, a config builder, a dotenv loader, anything that reaches the production entry point — changes `getenv()` for every test that runs after it, across suite boundaries when the suites share a process. The damage reads as an order-dependent flake and hides for months. **Snapshot the environment before such a test and restore it after.** And the asymmetry that makes this so hard to see: **cleaning up in teardown protects the next test and never the first.** A test that depends on the *absence* of a variable must clear it on the way **in**.
3. **The failure diff is an output channel.** A test that asserts on a credential, token or key prints the real value in full when it fails — into scrollback, into CI logs, into whatever a reviewer pastes. Codebases that carefully refuse to quote a secret in an error message routinely quote one in an assertion. **Assert on a derived property** — length, prefix, "not the plaintext", "not equal to what is stored" — **or clear the source so the comparison cannot reach a live value.**

4. **A guard that exists but runs too late is a latency gap, not a coverage gap — and the two have different fixes.** A missing test is written; a slow one is *moved*. An admin page had been throwing on every render for days. A test asserted exactly the invariant that broke and would have named it precisely — but it was test 4555 of 4875, four hours into a seven-hour suite, so in practice nobody had reached it since the defect landed, and the first witness was seven errors in an unrelated class four hundred tests earlier, which is why it read as a test problem rather than as a dead page. **For every invariant a slow suite protects, ask what it actually costs to check.** Reflection over two constants, a schema-versus-code comparison, a "every X has a Y" pairing — these need no database and no fixtures, and belong in whatever tier runs before a commit. The one that was moved went from unreachable-in-practice to **0.135 seconds**. When a suite is slow enough that people stop running it, its guards have already stopped guarding, whatever the coverage report says.

5. **The self-consistent codec.** A round-trip test — encode then decode, sign then verify, serialise then parse — proves only that the code agrees with itself. Against any external protocol, file format or partner API that is not the question; the question is whether it agrees with the *other side*. A payment-gateway codec passed a round-trip selftest for a day before anyone checked it against the vendor manual's own worked example (which printed key, IV, plaintext and the expected ciphertext and digest); a signature test reproduced the vendor's published example but its "sort order matters" sibling was vacuous — every key in the example started uppercase, so the two sort rules gave the same answer and the test could not fail. **For every external protocol the code speaks, find the counterpart's published example and a test that reproduces it byte-for-byte; then find the negative that can actually tell** (inputs the two rules order differently, a wrong key, a tampered digit) **and prove the test goes red when the vector is tampered.** A codec without a counterpart vector is a hypothesis with a green badge.

Method: enumerate the tests that touch the system's real configuration or entry points; confirm each restores what it changed. For every suite that asserts emptiness, find the sibling that proves non-emptiness. Record the assertion count alongside the test count in every claim, because *"N tests pass"* and *"N tests ran and asserted M things"* are different reports. For every external protocol, name the vendor-published vector the suite reproduces, or write "none — round-trip only".

**Grading.** A vacuous pass on a money path: **HIGH** — the code it was meant to cover has never been exercised. Environment contamination that reaches other tests: **HIGH** when the contaminating values are real credentials, **MEDIUM** otherwise. A live secret reachable in failure output: **HIGH**, and say it in the conversation with the rotation decision attached, per §0.11.

**The sentence to carry out of this sweep:** *green is a colour, not a measurement — quote the counts, and know which of them went up.*

Report line format: `S21 — T tests / A assertions quoted; V vacuous-pass risks found; E tests that mutate the runner environment, R of them restoring it; S secrets reachable in failure output; K of P external protocols pinned to a counterpart-published vector.`

## S22 — Surface completeness across step × outcome × audience. A STEP WITH NO SCREEN IS A STEP NOBODY CAN BE TOLD ABOUT, AND A SCREEN NOBODY HAS RENDERED IS A SCREEN NOBODY KNOWS IS BROKEN

The owner's question that defines this sweep: *"are you sure all gaps for [the] purchasing cycle, all combinations of them, each step has a UI and screen, to flag, show and confirm and catch whatever throws back, and every purchasing and checking step has a display showing admin or customer… how do you call this gap and how does our skill catch these gaps?"* In the system that asked it, ninety-five preview scenarios existed, forty-six of them admin, and **not one rendered an exception, alarm or badge**.

**Why the existing sweeps miss it, stated precisely, because each is close enough to feel like coverage:**

| Sweep | What it asks | Why it is not this |
|---|---|---|
| **S15** four-corner walk | do the corners *agree* about the object | a corner can agree perfectly and still have no screen |
| **S16** terminal-state accountability | does the state *end* somewhere a person can account for | satisfied by an alarm row that reaches *a* screen; never enumerates step × outcome × audience |
| **S17** control enforcement | can the setting reach the decision | about controls, not about surfaces |
| **S18** enumeration against the authority | is every *contract* combination verified | fields and pages, not faces |
| **S13** orphan capability | is the capability wired | a wired capability with no rendered state passes |

**The method is a matrix, and it is a different matrix from S18's.** Build it once, per transactional flow:

1. **Enumerate the steps** of the flow end to end, **including the reversals** — which are the half that gets forgotten, because the happy path is the one everybody demonstrates. For a purchase: offer, checkout, authorise, instruct or capture, settle, fulfil, deliver, close; then expire, cancel, refund, return, chargeback, and the late arrival that contradicts one of those.
2. **Enumerate the outcomes** of each step, and **`unknown` is a required column, not an edge case** — S21 and S20 both exist because a system that cannot say *"I could not tell"* says something false instead. The set: **succeeded · refused · timed out · partial · unknown · reversed after the fact.**
3. **For each cell, name the surface for each audience that bears the consequence** — typically customer and operator, sometimes a third (an accountant, a courier, a regulator). Where a cell genuinely has no audience, write that down rather than leaving it blank; a blank is indistinguishable from an oversight.
4. **A surface only counts if it satisfies all four:** it **exists**; it is **reachable by a URL or route somebody can open on demand**, without reproducing the situation that causes it; it **says what happened in words that audience can act on**; and for the operator it **says what to do next**. A log line is not a surface. An email is not a surface for the operator. A row in a table with no screen is not a surface.
5. **Mark every cell `OK` / `GAP` / `UNVERIFIED`**, exactly as S18 does, and treat `UNVERIFIED` as a task. A cell nobody has opened in a browser is `UNVERIFIED`, whatever the integration tests say — because an integration test asserts the *data* and has never once proved the page renders.

**The renderability clause, which is what makes this sweep different from S16 and is the part that gets skipped.** The states that most need a surface are the ones that only appear when something has gone wrong, and those are exactly the ones no fixture produces. **Demand a fixture per situational surface, not per page.** If reaching a screen requires reproducing a gateway outage, a lost callback or a ten-day-silent parcel, then in practice nobody has ever seen it — not the designer, not the reviewer, not the person who will have to read it at three in the morning. A coverage ratchet that counts pages and scenarios will report clean on all of them; widen it to count **conditional surfaces inside existing pages** — a badge, an alarm panel, an empty state, a disabled control, a refusal message.

**Grading.** A money step whose **refused**, **timed out** or **unknown** outcome has no operator surface: **HIGH**. A customer-facing refusal with no customer surface: **HIGH**, because the customer is stranded mid-purchase with their money possibly taken. A surface that exists but has never been rendered: **MEDIUM**, and it becomes HIGH the moment anything on the page is typed — the canonical case is a settings page that threw a `TypeError` on every request for days because nothing ever opened it.

**The sentence to carry out of this sweep:** *every way a purchase can go must have a face, and a face nobody has looked at is a rumour.*

### S22.1 — What this is called outside this skill, because hunting it needs the right words

**It has names. Several, one per community, and an auditor who does not know them cannot search for
prior art, cannot read the tooling that already solves half of it, and cannot tell a developer what
is missing in a word they will recognise.**

| Community | The name | What it gives S22 |
|---|---|---|
| UI design | **The UI Stack** — Scott Hurff, 2015: every component has **blank / loading / partial / error / ideal**. Missing ones are **empty-state** and **error-state gaps** | The canonical five-state checklist. Most teams design *ideal* and ship the other four by accident |
| Front-end | **story coverage** (Storybook), **visual coverage** (Chromatic, Percy, Applitools). The maxim is *"if it can render, it needs a story"* | The fixture-per-state discipline, already an industry norm - and the reason a preview catalogue is the right instrument rather than an invention |
| QA / test | **unhappy-path** or **sad-path coverage**, **negative testing**, and for state machines **statechart coverage**, split into **state coverage** (every state reached) and **transition coverage** (every edge taken) | Names the asymmetry precisely: happy-path coverage can be 100% while sad-path coverage is 0%, and one number hides the other |
| Combinatorics | **state-space explosion**, answered by **pairwise / all-pairs / n-wise coverage** (Combinatorial Test Design) | The honest answer to *"all combinations"*: the full cross-product is infeasible and nobody runs it. See the depth rule below |
| SRE | **actionable alerting** - the Google SRE rule that an alert which does not tell a human what to do is **noise**, not signal - plus **runbook coverage** and **observability gap** | Exactly why a log line and a digest mail fail this sweep. The industry already decided this and wrote it down |
| Product / internal | **operator experience**, **internal-tooling debt**, **back-office UX** | The vocabulary for arguing the work is worth doing, to somebody who thinks admin screens do not need design |
| Reaching the states | **fault injection**, **state injection**, fixtures and mocks; **chaos engineering** at the infrastructure tier | How the untestable-looking states get rendered without waiting for a real outage |

**Use these words in findings.** *"The refund-refused path has no error state and no story"* lands
with a front-end developer; *"S22 cell 4.3 is a GAP"* does not.

### S22.2 — How to hunt them, mechanical, in rough order of yield

1. **Grep the render guards.** Every conditional that wraps output is a surface: an emptiness check,
   a null check, an early return carrying a refusal reason, a match arm that renders something else.
   **Enumerate them and ask which has a fixture.** Highest-yield pass and pure grep - a conditional
   surface inside an existing page is the exact thing a page-level coverage ratchet cannot see.
   **And check what the fixture renders.** A preview that draws its own HTML beside the real page
   is a *hand-drawn twin*: it passes the ratchet, it looks rendered, and a theme written against
   it lands on markup the real page does not have. One catalogue had 32 admin previews and 23
   were twins - the order list and every order-detail state among them. Rule: **a preview renders
   the production renderer with fixture data, or it is UNVERIFIED**; assert by reflection that
   each scenario's renderer is a production page or controller class, never by eye. A twin is a
   wireframe - fine before the page exists, a liability the day it does - and its hub entry must
   say so.
2. **Walk the enums as statecharts.** **State coverage**: has each case a rendered surface?
   **Transition coverage**: has each edge one where it matters? The edges that run *backwards* -
   cancelled-then-paid, delivered-then-returned, refunded-then-charged-back - are where surfaces go
   missing, because forward edges get demonstrated and backward ones do not.
3. **Inventory the error paths.** Every catch, every throw that can reach a request, every refusal
   string, every non-zero exit. Each is an outcome. **A refusal reason that exists only as a string
   in a log is an error state with no error surface.**
4. **Empty states.** Every list, table and collection: what is shown at zero rows? Zero is the state
   a shop is in on **day one**, so it is the first thing a new operator sees and the least likely to
   have been designed.
5. **Read the alerting.** Every notifier, digest, cron exit code and alarm row: where does it land,
   and is that a screen somebody opens? Apply the SRE test - **does it say what to do?**
6. **Then, and only then, the cross-product** - bounded deliberately.

**The depth rule, because "all combinations" is not a plan.** The full cross-product of
step x outcome x audience x payment method x delivery method x destination x cart shape runs to tens
of thousands of cells and will never be walked. So:

- **Money paths at full depth.** Every step whose outcome can move, hold or lose money gets every
  outcome and every audience, enumerated exhaustively. This is a small set - it is the failure
  column, not the whole grid.
- **Everything else pairwise.** All-pairs coverage over the remaining axes catches the large majority
  of interaction defects at a fraction of the cells, which is the published result behind CTD.
- **Say which is which in the report.** A matrix that silently sampled is S18's original sin. State
  the axes taken at full depth and those taken pairwise, so the next reader knows what was not walked.

### S22.3 — Step 0: draw the decision tree before the matrix, because the matrix takes its steps from it

**The owner's instruction:** *"maybe you
should first draw a map of customer checkout choices of combination step by step, so you know how
many different paths and diversion of choices they can make each step… and to know best maintainable
non-messy way to set those paths."*

**The matrix as first written takes its step list as given, which is a sampling error wearing a
grid.** Steps enumerated from the code are the steps somebody already built; the tree enumerates the
steps the *customer* can take, including the branches nobody implemented. Do the tree first.

**Method.** One node per decision the customer makes or the system makes for them, in order, from
first intent to the last irreversible event — cart shape, identity, destination, delivery method,
payment method, payment execution, outcome, fulfilment, delivery, and the reversals. At each node
list **every branch**, not the common ones. Then:

1. **Count the leaves.** That number is the honest size of the problem, and it is usually an order of
   magnitude larger than the team's mental model. It is also the number the S18/S22 depth rule then
   bounds — money paths at full depth, the rest pairwise.
2. **Mark where branches converge.** *This is the maintainability question and it is the reason to
   draw the tree at all.* Fifty-four paths collapsing into six screens is a good design; fifty-four
   staying fifty-four is a mess that will be maintained forever. **Converge as early as the domain
   allows, and keep separate only what genuinely differs** — and write down which is which, because
   the next person will otherwise merge two paths that had a reason to be apart, or split one that
   did not.
3. **Mark every node where the screen changes.** That set, exactly, is the preview-fixture list —
   which answers *"what has to exist before this can be themed"* without anybody guessing.
4. **Mark every node where control leaves the system** — a hosted payment page, a carrier's site, a
   counter, a bank. Each is a **round trip**, and each needs the return path enumerated as carefully
   as the outgoing one. The classic miss is a branch that leaves and has no drawn way back:
   abandoned at the gateway, closed the tab after paying, the callback that never came.
5. **Mark every node that needs an operator gate** before the object can move on — and be explicit
   where the honest answer is *none*, because a blank reads as an oversight.

**What the tree catches that the matrix alone does not:** a branch that exists in the UI and has no
handler; a branch the code handles that no UI can reach (S13 from the other end); two branches that
were drawn separately and behave identically, which is cost with no benefit; and the branches that
only appear after something goes wrong, which are the ones nobody draws because nobody demonstrates
them.

**Then build the matrix from the tree's steps**, not from the code's. The tree is also the artefact to
keep: it is the one document a new person can read to learn what the system is *for*, and it dates
far more slowly than the code.

### S22.4 — Closure rule: the authority's error table *is* the outcome column

**The owner's statement of the closure condition:** *"every api or return
should have a ui or admin response on ui, and every combination of user possible behaviour or
situation of purchase cycle should have a catch on UI or admin… each combination may need a theming
of layout or flag design… to make sure no api response or flow got missed or unattended to on
screen and by system handling."*

That is the sweep's closure condition and it fixes the sweep's worst weakness. *"Enumerate the
outcomes"* invites invention, and an invented list is a sampled list wearing a suit. **It does not
need inventing: every provider has already enumerated its outcomes, exhaustively, in the error table
at the back of its manual.** Transcribe it.

**So S18 and S22 join here.** S18 reads the authority for the *contract*; S22 reads the same
authority's **error table** for the *outcome column*, and the join is one row per code:

| Provider code | Meaning, verbatim | **Handled** | **Surfaced** | **Designed** |
|---|---|---|---|---|

**The three columns fail independently, which is why one column is not enough:**

- **Handled** — the code reaches a deterministic branch. Not a `default`, not a fallback to a
  neighbouring meaning, not silence. *A code mapped onto another code's meaning is worse than an
  unhandled one, because it is confidently wrong.*
- **Surfaced** — a human sees it, on a screen, per S22's four tests. A log line, a digest, a cron
  exit code and a table row with no screen all fail here. This is the SRE **actionable alerting**
  rule: an alert that does not tell a human what to do is noise.
- **Designed** — it has a visual form somebody chose: which flag, which colour, which severity,
  which position, blocking or not. **An error rendered as raw text in the default font is handled
  and surfaced and still fails**, because the operator cannot tell at a glance whether it is urgent,
  and the customer cannot tell whether they still have to do something.

**This is also what makes theming estimable rather than open-ended.** The designer does not need a
layout per code — they need one per **surface kind**. Count the kinds, not the codes: blocking
refusal, non-blocking warning, informational note, badge on a list row, panel on a detail page,
empty state, disabled control with a reason. **Every code maps to exactly one kind, and the kinds
are a dozen.** Report both numbers: *N codes across K kinds* — the first is the audit's workload,
the second is the designer's.

**The same closure applies to the other direction — user actions.** Every action a user can take
that the system can refuse is an outcome with the same three columns: an invalid coupon, a
quantity beyond stock, an address the carrier will not serve, a method unavailable for the
destination, a session that expired mid-checkout, a double submit, a back-button replay. The
enumeration comes from the **render-guard census and the error-path inventory** (passes 1 and 3
above) rather than from a vendor manual, but the rule is identical: **handled, surfaced, designed.**

**What "no gap" means, stated so it can be checked:** every row of every authority's error table,
and every refusal the system itself can produce, has all three columns filled. Anything else is
`UNVERIFIED` and is a task. *A provider code with no branch is a bug; a branch with no screen is a
silence; a screen with no design is a message nobody reads in time.*

### S22.5 — What "handled" means, and it is not a `catch`

**The owner's definition, given against a scoring that had reported 26 of 26 handled:**

> *"Handled meant it is a closed loop and nothing dies quietly without a human actually noticing or
> taking action. Code may have a catch and quietly log it, but any exception should be noticed by
> admin dashboard, at least a flag or a badge for each situation. Admin may choose to diffuse or
> ignore, but it should be admin's decision, not quietly logged. You should determine whether the
> response requires actual follow up, so the UX for both admin and customer is fully informed — that
> the entire operation is a complete, or dismissed as an informed decision."*

**That is the terminal condition for this sweep, and it replaces the weak column outright:**

> **Every operation ends COMPLETED or DISMISSED-BY-A-PERSON. There is no third ending. "Logged" is
> not an ending.**

A `catch` that writes a log line is **not** handled. It is *caught* — a different, much weaker
property that only says the process did not crash. Scoring the two as one is how an audit reports
clean on a system whose every failure is invisible. **Score five columns, not three:**

| Column | The test | Failure mode it catches |
|---|---|---|
| **Caught** | the process does not crash, the request does not 500 | the weakest property, and the one most often mistaken for the others |
| **Classified** | **somebody decided, in advance and in writing, whether this outcome needs follow-up or is informational.** Not inferred at read time | the whole table treated as one severity, so nothing can be prioritised and everything is either noise or missed |
| **Raised** | if it needs follow-up, it reaches a **flag or badge on the screen the operator already opens** — not a log, not a digest, not an exit code | the silence this sweep exists for |
| **Closable** | a person can **dismiss it, and the dismissal is recorded** — who, when, why. Dismissing is an act, not an absence | an alarm that cannot be cleared becomes wallpaper within a week, and wallpaper is the same as silence |
| **Designed** | it has a visual form somebody chose: severity, colour, position, blocking or not | the operator cannot tell urgent from routine at a glance, so triage happens by reading everything |

**Classifying a vendor's code table, the shape that works:** one label per row from a set of
three — *customer retries* / *operator fixes* / *ours* — chosen in writing, with the customer
sentence and the operator surface each label produces. Then four rules the table will force:
**a default bucket** (the sandbox returns codes that are in no manual; unknown ⇒ ours, raised);
**text-decided codes** (one code, several messages — the classifier takes both); **the customer
never reads a parameter name** (ours and operator share one sentence); and **pre-checks beat
refusals** (every amount or state rule the vendor publishes is a guard before the call). Expect
*ours* to be the largest bucket — most of any gateway's table is malformed requests — and expect
at least one already-distinguished code to have the wrong sentence, because a specific sentence
is trusted and nobody re-reads it against the manual.

**"Ignore" is a legitimate outcome and it must be expensive enough to be real.** The owner's
formulation is exact: the admin may diffuse or ignore, *but it must be the admin's decision.* So a
dismissal path is **required**, and it must capture a reason and a person. A system that cannot
record *"I looked at this and decided it did not matter"* forces its operator to choose between
acting on noise and ignoring signal — and they will choose ignoring, every time, and then miss the
one that mattered.

**Classification is the auditor's own work, not the developer's.** For every outcome in the table,
say which of these it is, and say it in the report:

- **Needs follow-up** — a person must do something. Raise, and keep raising until dismissed.
- **Needs telling, not doing** — the customer or operator should know; no action. Show once.
- **Informational** — genuinely nothing. **Say so explicitly**, because a blank in this column is
  indistinguishable from an oversight, and the next auditor will re-derive it.

**And both audiences, always.** An outcome the customer bears — their payment refused, their parcel
returned, their refund past its window — needs a customer surface *and* an operator surface, and
they say different things. "Fully informed" in the owner's sentence means both, not either.

**The grading follows directly.** An outcome that needs follow-up and is only logged: **HIGH**, and
it is HIGH whether or not money is involved, because the failure is the invisibility rather than the
amount. An outcome raised with no way to dismiss it: **MEDIUM**, rising to HIGH once the count is
large enough that the screen is ignored. An outcome unclassified: **MEDIUM** — nobody has decided,
so nobody can be wrong yet, but nobody can be right either.

### S22.6 — Mode errors and invisible scope: a control must show what it will act on

**The defect:** if rows are selected and the
operator then re-sorts, re-filters or pages, **a naive list keeps the ticks against different
records** — so the button now acts on a set nobody chose and nobody can see.

**This class has names and they are old ones.** Raskin's *The Humane Interface* calls it a **mode
error** — the same action producing different results depending on a state the user cannot see — and
names modes a primary cause of human error. Nielsen's first heuristic is **visibility of system
status**. In list UIs it shows up as **scope ambiguity** and **stale selection**. Use those words in
findings; *"confusing"* is not a finding, *"this control has two scopes and neither is shown"* is.

**The rule: a control that acts on a set must make the set visible, unambiguous, and current.**

Three questions, per control that acts on more than one thing:

1. **What exactly will this act on** — the rows I can see, or everything matching a filter I set
   three screens ago? If the answer is not on screen, that is the finding. **Never one control for
   both scopes**: a header checkbox meaning *"all 312"* is how somebody marks three hundred orders
   dispatched intending fifty. Page scope is the safe default; *"select all N matching"* is a
   separate, visibly different, deliberate act.
2. **What happens to the selection when the view changes?** Re-sort, re-filter, change page size,
   page forward. **Silently keeping ticks against new rows is the defect.** Either clear the
   selection and say so, or carry it as an explicitly filter-defined set that survives paging and
   dies when the filter changes. Predictable beats clever: an operator who loses eight ticks and is
   told why re-ticks them; one who silently acts on the wrong eight never finds out.
3. **Is the mode itself visible?** This is the same defect outside lists, and it is worse where money
   is involved — **a test/sandbox gateway mode that looks identical to live is a mode error with a
   payment behind it.** Check every environment switch, impersonation session, draft-vs-published
   toggle, maintenance flag and preview mode: does the screen say which one it is in, everywhere it
   matters, or only on the page where it was set?

**Grading.** A destructive or money-moving action whose scope is not visible: **HIGH**. A selection
that survives a view change without saying so: **HIGH** if it feeds a bulk action, **MEDIUM**
otherwise. An invisible mode that changes where money goes: **HIGH**, always.

**The sentence:** *the operator should never have to remember what the screen is doing.*

### S22.7 — Do not invent admin UX; the conventions are settled

**The owner's instruction:** *"reference to shopify or woocommerce or whatever
best ecommerce standard, do not reinvent the wheel, only improve."*

**An operator who has run any shop already knows how an admin works.** Shopify, WooCommerce and
Magento converged decades of operator hours onto the same handful of shapes, and a product that
invents its own spends the operator's attention teaching them a layout instead of showing them their
orders. **Divergence is a cost paid on every single screen, forever.**

So when a surface from this sweep has to be designed, **name the established pattern it follows**
before drawing anything:

| Need | The settled shape |
|---|---|
| A list of records | filter bar, saved views/tabs, per-page selector, sortable columns, row checkboxes, a sticky bulk bar that appears on selection, paging with a total |
| Status | a **pill** with a colour and a word, consistent per state across every screen it appears on |
| An exception on a record | a banner at the top of the detail page and a marker on the list row — never only one of the two |
| A bulk action | select → action menu → **confirm sheet listing what will happen and to how many** → per-row result |
| A record detail | header with the key facts and the primary action, then panels, then a **timeline of what happened when** |
| Nothing yet | an **empty state** with one sentence and the action that ends it, never a blank table |

**The operator-desk pattern, four rules that a night of building desks kept re-finding
(2026-09-13 — mailing, postage, accounting, quick edit):**

1. **A queue, not a list.** A desk is *the number, the one sentence that says what a person does
   about it, and the link that opens exactly those rows*. A count that was already being computed
   by a worker and answered into a cron mail, an exit code or a digest is a queue with nowhere to
   put itself; give it the number, the sentence and the link. A zero reads as quiet, never as
   missing.
2. **Blank is a value.** *Nobody has told us yet* is different from `0`, which is a figure (free
   postage happens). A blank cell leaves the row alone; clearing a figure sets it back to *not
   known* and is logged like any change; an export carries the column empty and ruled, never as
   `0`. **Expected and actual never merge**: what the customer was charged, what the rate card
   predicts and what the receipt says are three columns, and the accountant needs the third.
3. **Value edits need compare-and-swap.** A grid drawn at 14:02 and saved at 14:09 posts what each
   cell held when drawn beside what was typed; a value another operator changed meanwhile is refused
   for that row, in words, never overwritten. A bulk action resolves *all N matching* to explicit
   ids once, against the same cap, before anything runs — it never re-runs a filter that may have
   moved.
4. **A hand-off needs a marker and an artefact.** A sheet that walks out of the building — to the
   carrier's upload page, to the accountant — stamps *exported_at* / *handed_to_accountant_at* and
   *by whom* the first time, and a re-download does not move the date; without the marker the only
   filter is *not yet done*, which re-exports rows somebody already uploaded, and a duplicate upload
   is the failure that costs money. The *tell the customer* box is default on, and unticking it is
   recorded on the row with a name, never silently absent.

**The class behind rule 1, walked 2026-09-13:** `grep -l 'exit(1)' tools/ops tools/worker` and
ask of each what a person *sees*. Three scripts answered *a log file*: a PDPA request past its
fifteen days, stored PHP in Hanna Code, a digital sale with no waiver evidence. Two surfaces
close the class — an order-scoped finding raises one `OperatorNotice` per order (badge on the
order, row on the desk, idempotent per order and case); a site-scoped one records *count + one
sentence* beside its heartbeat and the cron page draws it in red under the stopped workers. The
exit code stays for liveness; it was never a surface.
| A field the operator cannot use | disabled, **with the reason beside it** |

**Improve only where the domain genuinely differs**, and say why in the commit: a 字軌 invoice book,
a two-month filing 期, 取貨付款's money-at-the-counter, a carrier upload that takes a spreadsheet.
Those have no equivalent in a Shopify admin and are where invention is warranted. **A paging
control is not.**

**The audit question, then, is not "is this well designed?"** — it is **"which established pattern
is this, and if none, what does the domain require that the established one could not express?"** An
answer of *"it just grew that way"* is a finding, and it is the cheapest kind to fix while the
screens are still being built.

### S22 report line

Report line format: `S22 — F flows; S steps × O outcomes × A audiences = N cells, money paths at full depth and the rest pairwise (say which); K OK, G GAP, U UNVERIFIED; render guards found R, with a fixture X of R, of which T are hand-drawn twins (each UNVERIFIED); enum state coverage S/S', transition coverage T/T'; provider codes C across K surface kinds; caught A, classified L, raised R, closable X, designed D; outcomes needing follow-up that are only logged: N (each HIGH).`

