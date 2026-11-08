# Sweeps S23–S24 — event flow, contract tests

> Part of `references/sweeps/` (index: `README.md`). Split from the former `sweeps.md` on 2026-11-09 - text unchanged. Read every file in the folder per §0.9.

## S23 — Sequence and event-flow. A FLOW IS A SEQUENCE OF ARRIVALS, AND EVERY ARRIVAL CAN COME TWICE, LATE, EARLY, OUT OF ORDER OR NEVER

S15 walks one object through four corners and asks whether they agree *at each state*. This sweep
walks the same flows in **time**: who sends what to whom, in what order, and what happens when the
order is not the one the code was written for. A state machine review (doctrine §5/§6 in the
commerce skill; S16 here) says which transitions exist; this sweep says which *arrivals* cause them
and proves each arrival is safe in every order it can actually come.

**Method.**

1. **Draw the sequence, one per cross-boundary flow.** Columns are actors: the user's browser, this
   system's request handler, the database, each provider (payment, logistics, mail), each worker or
   cron, the operator's screen. One line per message, carrying the field that identifies the object
   (order id, provider transaction id, idempotency key) and the state write it causes:
   `browser → app: POST /checkout [order: draft→pending]`, `provider → app: notify [payment: pending→paid]`.
   Text is fine; the diagram goes **in the report**, one per primary-path flow at Screen
   tier, every flow at Walk. A sequence that exists only in the auditor's head is not evidence (S18).
2. **List every arrival this system does not control** — a callback, a webhook, a browser return
   post, a queue message, a cron tick, a provider query response, an admin click during a pending
   operation — and for each one fill six cells: **duplicate** (the same message twice), **out of
   order** (against every other arrival that can race it), **late** (after the ceiling, after the
   caller gave up, after a human already acted), **early** (before the state it presumes — the
   notify that lands before the local row is committed), **missing** (never comes; S12's ceiling),
   **malformed** (S11). Cite the file:line that handles each cell, or write `UNHANDLED`.
3. **Interleaving pairs.** For every two arrivals that can interleave — browser return vs server
   notify; callback vs admin cancel; reconciler vs callback; two workers on one row; a retry vs the
   original — name the lock, the compare-and-set predicate (S2) or the ordering rule that makes the
   outcome the same in either order. If the final state depends on which came first, that is a
   finding graded on the money or state consequence, even when each handler is correct alone.
4. **Cross-reference, do not duplicate.** The six perturbations here are the trigger list of the
   commerce skill's §6 transition audit and the timeout / retry / reordering rows of doctrine §7:
   fill them once, here, and cite this sweep there.

**Grading.** A primary-path arrival with no handler for
duplicate or out-of-order: HIGH. An interleaving pair whose outcome depends on order: HIGH on a
primary path, MEDIUM elsewhere. A late
arrival with no ceiling: file under S12 and cross-reference. A flow with no diagram in the report:
the sweep did not run on it; report `UNVERIFIED`, never "swept".

**Write the expected order as constraints, not as one sequence (2026-10-12).** For every interleaving pair,
state what must hold with `evidence.md` §E8's partial order — *exactly one terminal state; paid ≺ shipped;
notify and return in either order, the second a no-op*. A test that asserts one total order over events the
system does not order is flaky when it fails and vacuous when it passes. When a trace breaks a constraint,
report the first divergence, not the last symptom.

### S23 report line

Report line format: `S23 — F flows diagrammed (of F' on the map); A external arrivals × 6 perturbations = N cells; handled H, UNHANDLED U, UNVERIFIED V; interleaving pairs P, order-independent Q, order-dependent D (each a finding)`.

**S23.2 — the arrival vocabulary a request/response boundary needs (2026-09-17, from Saleor's
transaction events).** For every action a system takes against an external party, the arrivals
are a grid: the **request** (it can be sent twice), **success**, **failure**, **action required**
(a state the user must be shown), and the **reversal after success** that arrives days later and
must be recorded without pretending the success did not happen. A schema that has no name for
"more was taken than was owed" will call it success; a status enum with no `expired` will hold a
dead record open forever. Hold the S23 grid to the full vocabulary, and file the missing name as
a finding before the missing handler.

## S24 — Contract tests at every boundary. A FAKE THAT AGREES WITH THE PARSER PROVES THE PARSER AGREES WITH ITSELF

S11 asks whether a boundary validates what crosses it; S18 asks whether the authority was read per
field; S21 says a codec proven only against itself proves nothing. This sweep asks the question
those three leave open: **for each boundary, what test binds our side to the other side's actual
contract, and where did that test's fixture come from?**

**Method.**

1. **Enumerate the boundaries** — S11's `producer → consumer` list, both directions: inbound
   (callback, webhook, query response, import file, queue message) and outbound (the request we
   build, the form we post, the file we export). Internal boundaries count too: page → service,
   worker → table, module → module.
2. **Classify the tests on each boundary**, one letter per side:
   - **(a)** none;
   - **(b)** unit test with a hand-written fixture derived from our own parser or builder — the
     self-agreeing codec, S21; it is not a contract test for any external compatibility claim;
   - **(c)** fixture transcribed field by field from the authority document, with the citation
     (manual, version, page or section) in the test;
   - **(d)** a recorded real body from the sandbox or production, redacted, dated, with the provider
     version it came from;
   - **(e)** a live probe against the sandbox, run in this session, its output in the report.
   Only **c, d, e** are contract tests. Every primary-path boundary needs at least **c** inbound (the
    handler fed a real-shaped signed body, never the local method called directly — S15) and at
    least **c** outbound (the request builder asserted against the vendor's field table: required
    fields, lengths, character set, encoding, signature, amount format).
3. **For import/export, protocol and ecosystem compatibility, build the producer × consumer
   matrix.** Any app that claims to open, save, sync, import, export, embed, mount, print, upload,
   receive or send a format must name the independent producers and consumers it is compatible
   with: vendor tools, slicers, spreadsheet apps, browsers, mobile OS versions, webhook senders,
   document suites, plugin hosts, CLI versions, SDK versions, hardware firmware, or partner
   services. A round-trip through our own writer and reader is class **b** for that claim, even
   when it is byte-perfect; it proves only that our two halves share one assumption. At Screen
   tier, every externally-claimed boundary needs at least one **c/d/e** fixture from an
   independent producer or consumer, and the report names the omitted producers as `UNVERIFIED`.
   If no independent fixture exists, the product either narrows the claim ("our-exported files
   only") or raises a finding for an unsupported compatibility promise. The Mixomesh failure class
   is general: a root wrapper from a third-party producer pointed at related model parts; our
   self-round-trip fixture put meshes in the root, so the suite proved only the dialect we wrote.
4. **Consumer-driven on internal boundaries.** The consumer's test states the fields it reads; the
   producer's test asserts it emits them under those names; a rename breaks both (S9). A page that
   reads `resolution_note` from an array a service builds has a contract with that service whether
   or not anyone wrote it down.
5. **Version-pin every fixture.** A fixture that does not say which contract version it was
   transcribed from cannot be re-verified when the vendor revs (doctrine §1.3), and is an
   `UNVERIFIED` cell in S18's matrix from the day the vendor publishes a newer manual.

**Grading.** A primary-path boundary at (a) or (b) only, either direction: HIGH. An internal boundary at
(a) on a path that writes state: MEDIUM. A fixture at (c) or (d) without version and citation:
LOW, and the S18 cell it supports drops to `UNVERIFIED`.

### S24 report line

Report line format: `S24 — B boundaries (I inbound, O outbound, N internal); per boundary the class a–e per side (table); external producer × consumer matrices: P, independent fixtures C/D/E, UNVERIFIED producers U; primary-path boundaries below c: M (each HIGH); internal at a on a state-writing path: K; fixtures without version or citation: F`.
