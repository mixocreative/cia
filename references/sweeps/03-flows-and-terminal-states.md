# Sweeps S15–S17 — four-corner walk, terminal states, out-of-system enforcement

> Part of `references/sweeps/` (index: `README.md`). Split from the former `sweeps.md` on 2026-11-09 - text unchanged. Read every file in the folder per §0.9.

## S15 — The four-corner end-to-end walk. THE HIGHEST-VALUE DATA IN THE SYSTEM IS THE DATA THAT CROSSES ALL FOUR CORNERS

In any system, the four corners are the four places that each hold a partial truth about one object that carries the primary quantity: **the requester's surface** (the person who asked), **the operator / admin surface**, **the executor** (the component or party that carries the work out), and **the external record of truth** (what persists or settles outside the process), with the system's own store as the fifth point that all four claim to describe. In an editor or 3D tool: the viewport, the inspector and undo stack, the exporter or background worker, and the file on disk. In a job runner or pipeline: the submitter's CLI or page, the operator dashboard, the worker, and the output store or downstream consumer. In a shop: **the customer surface**, **the operator / admin surface**, **the fulfilment or logistics provider**, and **the payment provider**. Every other sweep looks at one channel; this one walks one *object* — a document or part, a job, a batch, an order, a booking, a shipment, a subscription period — through every corner it touches, in sequence, and asks at each state: **can all four corners answer what is true right now, and do their answers agree?** A state where one corner cannot answer, or answers differently, is a finding even when every function on the path is correct.

Method, per flow that changes the primary quantity — do not summarise this from the code's docblocks; trace it:

1. **List the states** the object can occupy, from first click to terminal (saved / exported / failed / reverted; queued / running / done / failed / cancelled; paid / delivered / refunded / cancelled / returned).
2. **For each state, fill four cells**: what the requester sees, what the operator sees and can *do*, what the executor believes, what the external record says. Cite file:line for the first two; the worker's state, the vendor field or callback, or the bytes on disk for the last two.
3. **Mark the disagreements.** A viewport that shows a part the saved file does not contain; a dashboard that says "running" for a job its worker abandoned; a customer page that says "pay at the counter" while the parcel is already collected; an operator queue that filters on a status the object no longer has; a provider that has moved on while the local row has not. Each is a finding with the class named (usually stale snapshot, dead control, or status-symmetry gap).
4. **Mark the unanswerables.** A state where the operator has no control, no queue row and no instruction is a finding: the system can enter a state a human cannot leave.
5. **Mark the reachability.** Walk the flow against the configuration production will actually run (the seed, the migration defaults, the flags as shipped) rather than a test fixture. A feature that is built, tested and unreachable under the shipped configuration is **CRITICAL** and is reported as such: every document says it is done and no user (no customer, in a shop) can use it.
6. **Name the settlement evidence.** For every state that claims the primary quantity moved — money settled, a file written, a job finished, rows committed — say which artefact proves it (a verified callback, a reconciliation query, an operator-recorded reference, a read-back of the written file, the output row the worker committed) and confirm no other signal is allowed to set it.

**Test consequence — this changes what a test is allowed to be.** Every test written for a flow that crosses corners must say which corners it covers, and the suite must hold at least one test per primary path that walks **all four**, end to end, with the external side faked at its own boundary (a signed callback body, a provider query response, a real file read back from disk) rather than by calling the local method that would have handled it. A suite made only of single-corner tests can be entirely green while the corners disagree — that is the exact shape this sweep exists to catch. When the project ships an end-to-end walk harness (headless scripts, browser walks, a scenario matrix), its coverage and its *unwritten* scenarios are part of this sweep's report line, not a separate concern.

**The environment must be able to render what the sweep claims to have walked.** Before reporting a four-corner walk as done, confirm the running system can actually reach each corner: the pages exist (a catalogue with no page rows makes every product URL a 404 and no walk of the customer corner is possible; an editor with no sample project has nothing to save), the operator can sign in, the provider sandbox or the worker answers. Seed gaps are findings of this sweep, not excuses for skipping it — they block the owner's own sign-off as surely as a bug, and they are usually one seeder run from fixed. Walk the corners in the running app, not only in the suite: a test renders a class in isolation, a browser renders what the operator will actually see.


**The runtime twin — walk the delta, not only the table (2026-09-24).** The four-corner table is
filled by reading, and it is this sweep's product. It is also a *claim about a running system*,
and the cheapest way to test such a claim is to run it: take the quantity the flow moves (the
document state, the claim on a job, the rows written, the balance, the seat, the stock), read it at all four corners, perform the
operation through the front door, read all four again, and assert the delta with its arithmetic
written out — `browser-walks.md` §12, plus the adversarial rows there, which are this table's
unhappy columns executed rather than reasoned about. It is the same table, run. Corners that
disagreed on paper either disagree in fact, and the finding is now CONFIRMED with artefacts, or
they do not, and the reading was wrong — both outcomes are worth more than the prediction.

Every ladder fills rows of the evidence ledger (`reporting.md`); every cell the tier did not
execute stays UNVERIFIED there. That is how a reader tells the table that was read from the
table that was walked, and it is the one distinction this sweep could not previously make.

Report line format: `S15 — walked N flows × M states; four-corner table in the report; K disagreements, J unanswerable states, R reachability findings. · runtime: L ladders run, A of 9 adversarial rows (`browser-walks.md` §12); C corner cells proved by artefact of N.`

## S16 — Terminal-state accountability. EVERY FLOW MUST END SOMEWHERE A PERSON CAN ACCOUNT FOR

Where S15 asks whether the corners *agree*, this asks whether the object ever *ends*, and whether anyone is told when it ends badly. The owner's instruction, which is really an audit rule: *"No delivery or transaction should allow go dead quietly with loose ends, all ends must be tied and traceable"*, and *"anything system cannot handle must hv badge or flag in admin panel of order management page to let admin handle and notice."*

The defect this catches is not a wrong value. It is an object that stops moving and nobody finds out: the one class where **every function on the path is correct, every test passes, and the loss is real**. It hides from S1–S15 because there is nothing to disagree with — there is simply no further event.

Method, per flow that changes the primary quantity:

1. **Enumerate the terminal states, then enumerate the non-terminal ones.** Any state an object can occupy that is neither terminal nor guaranteed to advance is a candidate finding. For each, name the thing that advances it: a callback, a worker, a clock, a human. "It will arrive" is not an answer; name the code.
2. **Kill each advancer in turn and ask what happens.** The callback never arrives. The worker is not scheduled, or throws on its third item and stops. The provider answers once and never again. The human never looks. For each: does the object eventually reach a state someone can act on, or does it sit? An object that sits forever is a **silent death** and is HIGH at least.
3. **Follow every swallowed signal.** A `catch` that logs and returns, a queue row marked done on a failed send, a `return false` a caller ignores, a retry budget that simply runs out. Each is a place where the system decided something and told nobody. Ask where the *last* copy of that fact lives, and whether anything reads it.
4. **Check both halves of a two-fact truth.** Where a state claims two things happened — the goods moved *and* the money arrived, the file was delivered *and* the entitlement was granted — confirm they are two records that can disagree, and that a disagreement raises something. A system that infers the second from the first cannot detect the case where only one is true.
5. **Then check the notice lands on a working surface.** This is the half that is usually missing. An alert row nobody queries, a log line, an email to an address nobody reads, a table with no page — none of these is a notice. The test is: **is there a screen the operator already opens every day on which this thing becomes visible?** Name it for this system: the job dashboard in a runner, the run history in a pipeline, the status bar, problems panel or the object itself in an editor, the order list and the order page in a shop. A capability to handle the exception, on a page nobody opens, is a dead control (S5) wearing a different hat.
6. **Report the unattended set.** Every state where the object can stop with no advancer and no notice, as a table: state, what should have advanced it, what the operator would see, how they would ever find out. An empty table is a real result; an absent table means the sweep was not run.

**Grading.** The primary quantity lost with no signal — money or goods, a user's saved work, a job's result, committed data: **CRITICAL**. An object that can sit forever but is recoverable once noticed: **HIGH**. A notice that exists but only in a log or a table with no screen: **HIGH** — by the owner's rule that is not a notice at all. A notice on a screen nobody has a reason to open: **MEDIUM**.
**S16.2 — the dispute row (from the chargeback guides, 2026-09-15).** Precondition: the system
takes card payments; otherwise `no sites on the map` — but carry the general form, which is work
that arrives from outside with a deadline the system did not set (a takedown notice, a
data-subject request, an SLA ticket, a security report) and needs its evidence collected before it
arrives, its deadline as a ceiling with a notice, and repeat senders flagged. A chargeback is work
that arrives from outside with a deadline nobody in the shop set: the acquirer's window to answer
(7–10 days is common), after which the money is gone by default. Three things the S16 table must
show for it, whether or not a "chargeback path" exists in the code: **(a) the evidence is
collected at placement, not when the dispute lands** — the consent text id, the address, the
client address and user agent, the delivery scan, the download record; sixty days later none of
it is obtainable; **(b) the response deadline is a ceiling with a notice**, on the desk, at
T minus a few days, not an email to an unread inbox; **(c) a repeat disputer is a flag** on the
next order from the same address or card fingerprint. A shop whose answer is "the acquirer writes
and we answer by hand" has the ceiling in a person's memory - say so in the S22 row, as
`UNVERIFIED`, never as handled.


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

**2b. `rowCount()` may mean *matched*, not *changed* — check the connection before trusting the number.** MySQL's default reports rows the `SET` actually changed; with `PDO::MYSQL_ATTR_FOUND_ROWS` it reports rows the `WHERE` matched, and a codebase may enable that deliberately — one did, to stop idempotent re-saves reading as *"not there"* (`fb64069e`). Rules 2 and 2a survive either setting **only because the precondition is in the `WHERE`**: a row that no longer qualifies is not matched, so it is not counted, whichever semantic is on. What does *not* survive is any code reading `rowCount() === 0` as *"nothing changed"* — under `FOUND_ROWS` a no-op re-save matches and reports 1. A test asserting the old semantic was found red, unreached, at about test 4700 of a six-hour suite. **Grep the connection for `FOUND_ROWS` before writing or auditing any row-count logic, and if the contract needs "nothing to change" to read as zero, put that in the `WHERE` too** — NULL-safely, with `<=>`, because the columns compared are usually the ones that start NULL.

**2c. Validate per cell, not per submission.** One bad value must not reject the other forty-nine.
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
or end user gets a **"tell them" checkbox, defaulted on, with the unchecking recorded — who and when.** A
customer who was never told must be distinguishable from one somebody decided not to tell. The
checkbox writes *intent*; the sending stays with whatever durable sweep already sends, because a
send-inside-the-click makes the customer's message depend on the operator's browser staying open.

**S16.3 — a status that summarises children is resolved, never written (2026-09-17, from Sylius's
order workflows).** A mature commerce engine keeps one machine per child row (each payment, each
shipment) and *resolves* the parent's summary states — partially paid, partially shipped — from
the children on every child transition, through listeners, never through a form. The generic
rule: **any field that summarises other rows is a function of those rows, recomputed when they
move; a code path that writes it directly is a finding**, because the first time a child moves
without the parent following, two readers see two systems (S15). The same workflow reverses on
cancel what placement did (a usage counter incremented on place is decremented on cancel) and
snapshots at placement the facts a later reader must not see change. Ask of every counter which
event decrements it, and of every printed fact whether it is the record's copy or a live join.

**S16.4 — every transition names its preconditions, and every precondition has a sentence the
person sees (2026-09-17, from Vendure's order process).** Vendure refuses each transition with a
named reason — *cannot transition to payment when the order is empty / without a customer /
without a shipping method / due to insufficient stock; cannot ship without settled payments;
cannot cancel unless all fulfilments are cancelled* — and the shape generalises: the guard
belongs on the **transition**, not on the button that usually triggers it (a guard on the button
is S17 the moment a second caller exists), and every refusal carries a message the user reads
(a guard with no sentence is a refusal met as a page that does nothing, S22). It also models
*change after commitment* as a state of its own (`Modifying`, `ArrangingAdditionalPayment`) with a
row that links the change to the money or the reversal it caused. Ask whether this system lets a
committed record change; if it does, whether the change is a row with a link or an edit nobody
can account for.

*Two ratchets from the day it was first run whole-shop (2026-09-17).* **(a) A locale-coverage test
keyed on the message table proves the table, not the code.** The shop's test walked every code in
`codes()` through every locale and was green while eight reasons thrown under `src/` had no code at
all and fell through to the developer's English. The ratchet that holds is keyed on the *throw
sites*: scan the source for every `throw new <Refusal>('<reason>'` and assert each reason is in the
table (exempting the ones that route through another table, by name, with the reason written
next to the exemption). **(b) A compare-and-swap repeats every predicate of the query that chose
the row.** The expiry sweep selected candidates on three conditions and claimed each with an UPDATE
that re-checked one; the other two were the ones a concurrent writer could change (a pickup block,
a vendor instruction row). Ask of every conditional claim: does its WHERE equal the SELECT's, or
only the clause the author thought was racy?

## S17 — Controls whose enforcement point is outside the system. A SETTING THAT CANNOT REACH THE PLACE THE DECISION IS MADE IS A LABEL, NOT A CONTROL

The owner's question that defines this sweep: *"How do we restrict user use which chain by toggle? Or do we trust our toggle auto reflects payment gateway setting?"*

S5 asks whether a control reaches a consumer. S13 asks whether a capability has a caller. **Both search this codebase, and both pass when the consumer is somebody else's software.** That is the hole. The shop had a per-carrier admin toggle, stored in its own table, read by its own storefront, with tests. The customer chose their carrier on a page the *payment gateway* rendered, from a list the gateway's own back-office controlled, and the request field the shop sends has no parameter that can express the restriction at all. Every local check was green. The toggle governed nothing.

The signature: **a decision that happens on a third party's surface — an OAuth consent screen, an OS permission prompt, a printer or slicer's own settings, a hosted checkout, a hosted picker, a courier's booking page, an app-store purchase flow — while a setting on our side claims to shape it.** Outside commerce the same shape is an app's "share anonymous usage: off" toggle while the bundled SDK reads its own consent flag, or an export setting the target application re-decides on import.

Method:

1. **List every decision the user makes outside your UI.** Hosted payment pages, store or locker pickers, carrier selection, consent screens, plan choosers, anything reached by a redirect or an embedded widget. For each, name the redirect or handoff in your code — that call is the entire surface you control.
2. **For each such decision, find the local setting that claims to constrain it.** An admin toggle, a feature flag, a catalogue of options, a config file. If none exists, the decision is simply theirs and that is fine — say so and move on. If one does exist, it is a claim, and the next two steps test it.
3. **Open the provider's specification for the request you actually send, and find the field.** Not their marketing page, not a blog, not your own wrapper's docblock — the request-field table in the integration manual, by page. Ask one question: **can this request express the restriction the setting claims?** Quote the field, its permitted values and its defaulting rule into the finding. Very often the answer is that the field has two coarse values where your setting has six fine ones.
4. **Find where the provider says the real decision lives.** Manuals usually state it plainly in a sentence nobody reads — a merchant back-office setting, an account-level activation, a per-sub-type approval. Whatever it names is the actual enforcement point, and it is outside your repository and outside your tests.
5. **Then decide which of three shapes the system is in**, and say which in the report: **(a) enforceable** — the request can carry the restriction, so wire the setting to the field and test it; **(b) not enforceable, and the setting is a lie** — either delete it or redefine it as "what we accept", which then requires a rule for what happens when the provider returns something outside the set (S16 applies: a badge, not a silent accept); **(c) enforced by the provider's back-office** — the setting must be documented as a mirror of a console value, with the console step in the deploy prerequisites, and something must reconcile the two or they will drift silently.
6. **Check the return path for values your local set does not contain.** Whatever the provider's surface offers, it will one day return an option your configuration says is off. Find the code that receives it. If it accepts it silently, that is the finding — the toggle is not merely inert, it is now producing state the operator believes cannot exist.

**Grading.** A setting that constrains a primary-path decision — money, carrier or fulfilment, data sharing, access, what the exported file contains — and provably cannot reach the decision: **HIGH** — it is a control the operator will make decisions with. Silent acceptance of an out-of-set value returned by the provider: **HIGH**. A mirror-of-console setting with no reconciliation and no deploy step: **MEDIUM**, raised to HIGH once two operators can edit either side. A cosmetic setting correctly documented as cosmetic: not a finding.

**The reading rule this sweep exists to enforce:** when a provider's manual is on disk, *read the field table for every field you send*. A wrapper's docblock describing what a field does is your own summary of their document and carries none of its authority — several of the defects this sweep was written from were wrong summaries written confidently by the same people who later audited them.

Report line format: `S17 — N off-system decision points; K settings tested against the provider's field table; findings by shape (enforceable / lie / console-mirror).`

