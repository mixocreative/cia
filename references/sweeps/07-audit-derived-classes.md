# Sweeps — audit-derived classes: dated lessons from real audits, each filed under the sweep it names

> Part of `references/sweeps/` (index: `README.md`). Split from `06-event-flow-and-contracts.md` on 2026-11-09, with S22.7's dated 2026-09-13 / 09-14 gateway lessons moved in; text unchanged. Read every file in the folder per §0.9.

## Audit-derived classes — each one a site to enumerate under the sweep named

Every class below survived a green fast suite and a clean analyser in a real audit, and each is a
site to enumerate under the sweep it names (`SKILL.md` §0.9 points here; until 2026-10-22 these
blocks lived in `SKILL.md`). Each is written **invariant first**: the domain-neutral rule and what
to enumerate, then the original instance — marked *e.g. (shop)* where it came from the commerce
project most of these dates audited (mixoweb) — and, where natural, an instance from another kind
of system. The instance illustrates; the invariant is what gets swept, in every domain. A class
whose precondition the system lacks (no forms, no scheduler, no second factor) is answered `no
sites on the map: <row>`, per the reading rule above.


### 2026-09-13 / 09-14 — a shop with three payment gateways (moved here from S22.7 on 2026-11-09)

*The dated blocks below (2026-09-13 / 09-14) were learned on a shop with three payment gateways;
each carries its general rule in bold. Precondition for the gateway- and provider-specific ones:
the system integrates more than one external provider of the same capability (several gateways,
carriers, storage backends, model APIs, print services).*

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

**Credentials from a screenshot are a hypothesis (2026-09-13, PAYUNi).** A Hash Key read off an
image had one glyph wrong (lowercase l for capital I); the codec encrypted cleanly and the vendor
answered `DEF01007 Hash比對不符合`. The proof of a key is a **live no-op request** — a 交易查詢 for an
order that cannot exist — answered *inside a verified envelope* (`QUERY03001`); an unencrypted
refusal names which of the three values is wrong. Build that probe before the checkout, put it on
the gateway test page, and try the l/I, O/0, 1/l variants yourself before asking anyone to paste.
**Vendor docs behind an SPA (ShowDoc, docsify):** pull the page source through the app's own API
(`/server/index.php?s=/api/page/info`, `page_id`) — the rendered page is empty to a fetcher and a
copied table drops the cells that carry the money rules. Cite page ids, keep the markdown in the
gitignored vendor-docs folder, generate the status map and its audit document from one script.
**One vendor's rule, applied to the next, is a bug (2026-09-13).** NewebPay's order number is
unique forever, so the shop froze every pickup order after one hosted-page visit; PAYUNi only
refuses a repeat within ten minutes, and the same freeze would have left an abandoned PAYUNi page
unpayable for good. When a third provider joins, walk every `if pickup` / `if provider` guard and
ask which vendor's manual it came from — a guard with no citation belongs to one vendor only.
**The third provider's checklist (2026-09-13, PAYUNi, found by a Screen-tier pass forty minutes
after the merge).** A new provider inherits every *per-provider* safety net the first two grew,
and each one is a separate place to forget: **(a)** the expiry sweep's hold-back for a notification
queued but unread — three providers, three hold-backs, the third was missing and the drainer
(5 min) is slower than the expirer (1 min); **(b)** the pull behind the push — a poll of awaiting
orders when the vendor documents no notify retry, keyed to what the vendor's "no such order"
answer costs (PAYUNi: nothing; NewebPay: a four-hour lockout after too many 查無, so that one
needs the order to *record its gateway at redirect time* instead of a blind poll); **(c)** the
operator note that names a console — grep every sentence naming the first vendor's menu and ask
whether it renders for the new vendor's rows; **(d)** the customer note under the Pay button, which
must read the request's own switches, never a fixed sentence per delivery method. Walk the list
by grepping the *first* provider's name across `tools/worker`, the admin notes and the storefront
copy, and asking of each hit what the third provider does there.
**The audit reads the gateway off a row that does not exist yet (2026-09-13, S16 × S21).** A
settlement audit took the vendor from the *payment* row; an awaiting order has none (it is written
at settlement), so the audit's own "the notification never arrived" branch was reachable only by
a test fixture that gave an awaiting order a payment row production never writes. **A test that
hands its subject a shape production cannot produce is a fixture-shaped pass**: for every
"what if X never happened" test, check where the fixture's rows come from in production and
whether *that* writer runs before X. The fix was a column written at redirect time, and the lesson
generalises — an object waiting on an external signal must record whom it is waiting on, or
nothing can ask.
**A code-only Screen pass while the full suite holds the database is worth running (2026-09-13).**
Two HIGHs and a vacuous test in forty minutes, none of which needed a database, a browser or a
sandbox; the DB tests written for the fixes are queued for the slow filter and named as unrun
(S8). Do not wait for the environment to be free to read the code.
**The first provider sized the column (2026-09-13, S21 × the third-provider checklist).** A ledger
column was `VARCHAR(8)` because the first gateway's action codes were one letter; the second
gateway's `newebpay_close_refund` is twenty-one and had never been written by any DB test - the
first production card refund on the primary gateway would have thrown "Data too long" at the
claim. The third gateway's test was the first to write it. **When a new integration joins, grep
every `VARCHAR(n)` with n ≤ 16 on every table it writes to, and for every money path on the
*existing* providers ask which DB test drives it end to end through the store** - a unit test
with a fake ledger proves nothing about the column. And when a walk runs green on a state
machine, read its `out_of_order` lines as findings: a 門市關轉 after 到店 was refused as a
backward step by an ordering rule written for another carrier's vocabulary, the letter still went
out because the event row is written first, and only the alarm was missing.

**An `OK` in the surface matrix cites a renderer; only S15 proves the row reaches it (2026-09-13,
Walk tier, S22 × S15).** The instruction cells - the "how to pay" mail, the order-page panel, the
admin panel - were `OK` with a preview fixture each, and empty in production for the primary
gateway: its 取號完成 post was read for the store block only and the number acknowledged and
thrown away; the shop's own 30-minute card clock then cancelled an order the vendor had given
days. Two HIGHs behind one `OK`. **Rule: a matrix cell is `OK` only when the S15 row for that
state names the write that fills it** - the fixture proves the screen, the four-corner walk proves
the data. And the class re-walk that followed found the same post's lost-in-the-browser case had
no advancer at all, though the vendor's query carried the number the whole time (`PayInfo`,
§4.3.2 註2): **when a browser POST is the only carrier of a fact, the vendor's query is read for
the same fact and a poller writes it.** Second lesson from the same evening, S20: **a class fix
applied to the provider under audit is not a class fix.** The blind-run finding of the morning
went onto the two workers of the new provider and not the six older ones with the identical
shape; "its whole class gets re-walked" means every worker with a `failed` counter, listed by
`grep`, not the ones in the diff. Third, §7 crash recovery on a two-statement intent: "write the
row, then extend the deadline" on three paths - a crash between the statements leaves a customer
holding a live number under the shop's shorter clock; the fix was not a transaction but making the
sweep read the row's own expiry, so the second statement stopped being load-bearing.

**"Handled" needs a surface too, and an audit table with no page is not one (2026-09-14, S22
after-resolve).** The exceptions panel had a "Mark handled" button that asked *what did you do
about it?* and sent the answer to the credential audit log - a table whose admin page was still a
wireframe. So the closing was recorded and invisible: the next person to open the order saw
nothing, and a problem dealt with looked exactly like a problem that never happened. The matrix
had said `OK` for the exception row because the *open* state rendered; nobody had asked what the
screen shows one second after the button. **Rule: for every operator action that closes a state,
walk the screen after the click** - the loop is closed when the closing is visible where the
problem was, with who, when and what they did; a write to a table nobody reads is the report
storey of silence wearing a success notice. Second, the ratchet lesson: a coverage test keyed on
Page classes or scenario enums cannot see a *conditional section inside a covered page* - the
panel that renders in one state only is exactly the surface nobody previews. Mark such sections
(`data-panel="…"`) and ratchet on the markers: every marker on disk must be rendered by some
scenario. Third, S14.1 again: nine plan rows read "patch ready" while the patches had been merged
for two days, and the gate check ("every row ticked") would have been answered wrong by anyone
reading the plan instead of `git log -S`. **Drift check runs against the commits, not the prose.**

**A flake with no evidence in its failure message is the proof storey dying quietly (2026-09-14,
S21 / S12.1).** A CLI-worker test had failed "about one run in three" for a month with the message
`processed=0 stop=no_available_jobs`, and the gap register said *not investigated to root* with
three guesses and two cheap fixes, "neither done because the flake is harmless". It failed once
more at the end of a seven-hour run, on the commit that was to be the gate, with the visibility
wait that was supposed to close guess one already in place — so guess one was wrong and the other
two were still guesses. Twenty-five isolated re-runs passed, which proves only that the failure
needs the seven hours. **Rule: a test that spans a boundary (subprocess, second connection,
container, clock) asserts with the other side's view in the message** — the row as the server
holds it next to the server's own clock, the process list, the exit code and stderr — so that the
first recurrence is the investigation and not another retry. A retry that passes is not a root
cause; "harmless" is the word the register uses for a defect it has stopped looking at. File such
a test under S12.1 as a failure mode of the *proof* (detection: the message; surface: the
register row; recovery: never "re-run until green").

### 2026-10-07 — the mixoweb audit fix

- **S1 — a form value read at render and written back on save.** A form that posts back a field it
  only displayed overwrites any change another writer made to that field while the form was open.
  Enumerate every form field that writes a column something else also changes (a counter, a
  balance, a limit, a window, a status, a list another panel edits); each must carry what it was
  rendered with and the write must compare under the lock (refuse "changed since you opened it"),
  or the field must be left out of the write when unchanged. *e.g. (shop):* a price form that also
  posted the stock it showed set the stock back to that number over a sale made while the form was
  open. *Also:* a project-settings dialog that re-saves the layer list it showed, discarding a layer
  another panel added meanwhile.
- **S2 — a `SELECT … FOR UPDATE` on a key that does not exist yet, inside a post-lock re-check.**
  InnoDB takes a gap lock, and unrelated writers on neighbouring keys block until timeout (error
  1205). After the row lock is held, a re-check of an idempotency key is a plain read. Probe: two
  connections, two different keys, `innodb_lock_wait_timeout = 1`.
- **S2 / S12 — an idempotency key that names the payload instead of the request.** A key built from
  the operation's values makes two genuine requests that happen to carry the same values one
  request, and the second reads as done. Key by a per-render request id (or the approval id);
  report a replay as a replay, never as a fresh success. *e.g. (shop):* `refund:<order>:<amount>`
  made two genuine refunds of the same amount on different days one refund, and the second press
  read "refunded". *Also:* an export job keyed `<scene>:<format>` that swallows a second export
  requested after the scene changed.
- **S2 — check-then-record limits.** A rate limit or quota that counts and then inserts lets N
  concurrent requests at the limit all pass. Record first, then count.
- **S12.3 — a switch and its safety stamp in separate autocommit statements.** Turning a feature
  off and stamping its cutoff (a token cutoff, a cache epoch) in two statements can leave it off
  with no cutoff, so the next switch-on revives every old token. One statement or one transaction;
  a failure changes nothing and propagates.
- **S3 — fail-closed but mis-worded.** A check that cannot read and answers with a confident false
  fact is closed but lies; log it and refuse with the true sentence ("could not check") and its own
  code. *e.g. (shop):* a dispute check that could not read answered "there is a dispute on this
  order". *Also:* a licence check that cannot reach its server and says "your licence has expired".
- **S5 / S18 — readers that assumed one row per parent after a migration allowed many.** When a
  unique key is replaced by "one live row" (void and reissue, versioned rows, soft delete), grep
  every `WHERE parent_id = ?` without an order or status filter; each must say live-first (`ORDER BY
  status = 'voided', created_at DESC LIMIT 1`) or that it wants history.
- **S8 / S21 — a derived count that puts one row in two states.** A card counting two flags
  independently (`notified` and `dismissed`) double-counts a row that is both, while the table shows
  it once. One precedence, one function, used by the counts, the filter and the row label.
- **S21 — a secret test made vacuous by the code under test.** A planted secret that the output
  normaliser happens to mask (hex, digits) passes "no secret leaked" with the masker removed. Seed
  values the normaliser cannot touch and prove the test red by removing the mask.
- **S21 — a framework that turns the exception into a 200.** A test that asserts a `404` exception
  class was thrown proves nothing when the (admin) framework catches it and answers 200 with an
  empty body. Assert the HTTP status through the real front controller, or set the status before
  the throw and pin that.
- **S21 — analyser and suite scope listed by hand.** A `phpstan.neon` (or tsconfig, mypy) path list
  written by hand covered 21 of 53 module directories; a test must fail when a source directory is
  missing from it. Likewise two test files declaring the same global class name only crash the run
  that loads both (the fast suite stays green): a fast test must scan for the clash.
- **S22.9 — dead `data-action` markup.** Already listed; the re-walk found it on a providers page
  every card rendered. Scan all of `src/` for `data-action` (or the framework's handler binding)
  with no listener anywhere, not only the page in hand.

### 2026-10-09 — the mixoweb approve-by-link audit fix (five audits plus review-capped residue)

- **S11 — a sanitiser stricter than the consumer it protects (parser differential).** A validator
  that parses untrusted input more strictly than its consumer passes every lenient form the consumer
  accepts and the validator's library refuses. Enumerate every validator of untrusted markup, URLs
  or paths; normalise exactly as the consumer parses (WHATWG URL, the HTML tokenizer, the
  filesystem), and add one case per lenient form the consumer accepts that the validator's library
  refuses. e.g. an off-site URL check decoded HTML with `html_entity_decode()`, which needs the
  `;`; browsers and libxml decode `&#58` and `&#x3a` without it, so `https&#58//tracker/p.gif`
  passed and rendered.
- **S2 / S9 — an identity compared outside the store with a different equality than the store's.**
  Every lock name, dedupe key and guard that compares ids in code canonicalises them the way the
  store compares them, or resolves the id from the store first. *e.g. (shop):* `product.id` was
  case-insensitive and trimmed trailing spaces (utf8mb4 `_ci`, PAD SPACE); a named lock and a
  pending-publish guard keyed on the raw input made `PROD_x` and `prod_x` two products in the app
  and one in the database. *Also:* paths on a case-insensitive filesystem (`Part.stl` and
  `part.stl` one file to the disk, two to the app's cache), user names compared before Unicode
  normalisation.
- **S1 / S23 — a send-once key bucketed by a clock in another zone than the schedule that writes
  it.** Bucket in the zone the schedule runs in, test with the instants the real clock produces,
  and make a send the log already held say so. e.g. a reminder keyed `date:am|pm` in UTC, run by
  cron at 09:00 and 17:00 Taipei (01:00 and 09:00 UTC), gave both runs one key, and the mail log
  dropped the second as a duplicate while the job printed "1 waiting". Tests fed UTC times
  production never produces.
- **S5 / S20 — an optional collaborator left out at one construction site.** For every class with
  an optional, behaviour-carrying parameter, list every `new X(`; a scheduled path is proven by
  running the worker as a process in a test. e.g. a housekeeping class whose `?SlotRepository
  $slots = null` skips ending upload slots was built with it by the page and the kernel and without
  it by the 15-minute worker, so on the schedule nothing ended and the quota stayed spent.
- **S20 / S22 — a health check whose only reader is a machine.** Every health row has a human
  surface — the dashboard and the page it names — with a preview fixture, and a reader that throws
  is shown as "could not be read", never as an empty healthy list. e.g. two checks were read only by
  AI tools (AI access ships off), so red reached no person.
- **S3 / S16 — mirror operations with asymmetric failure handling.** For every pair (do/undo,
  approve/restore, grant/revoke, cancel/reinstate, migrate/rollback, an editor command and its undo)
  diff their catch blocks and their audit rows; the reverse path needs the same "stopped part way"
  record. e.g. the approve run caught `Throwable` and recorded "may have started"; its undo let a
  throw escape past the audit row, so a part-done undo read "changed since" with nothing saying what
  was put back.
- **S3 — a second factor skipped when its channel is missing.** A missing factor channel (no email,
  no phone, no enrolled device) refuses with a sentence; it never passes. e.g. an admin account with
  no email was handed to the gate as "not logged in", so it skipped the emailed code and entered on
  the password alone.
- **S2 / S16 — the closing UPDATE of a long operation with its row count unchecked.** Every guarded
  state transition that ends a long operation checks the row count and undoes its own side effect
  (the file) when it lost. e.g. a streamed upload that finished after the sweep ended its slot ran
  `UPDATE … WHERE state = 'receiving'`, changed nothing, and still answered "Received" with an audit
  row.
- **S5 — an eligibility predicate narrower than its own docblock.** Read the docblock's stated
  predicate against the code at every eligibility gate; a mismatch is a finding even when no test
  fails. *e.g. (shop):* `isEligible()` was documented "paid and dispatched" and checked only "paid",
  so a return could be opened before posting; the refunded unit went back on sale while the pick
  list still said post it. *Also:* a "can export" gate documented "saved and validated" that checks
  only "saved".
- **S22 — an untrusted stored value inside a panel presented as the system's facts.** Every value in
  a facts panel is either read now from the store or labelled and quoted as the requester's words,
  and the hint claims "read now" only for what is. e.g. the approval page's "What this is" printed
  the assistant's raw target param ("It acts on sku …") under a hint saying "the facts above are
  read now"; a nonexistent SKU like `Checked-by-the-shop: SAFE` is still stored.
- **S21 — a test that hands the unit the value its caller looks up.** A presentation or lookup bug
  needs one test through the real caller with two rows that differ in what is looked up. e.g. the
  download streamer's tests passed the asset in directly, so the desk's lookup (the SKU's first
  file, for a SKU that sells many) was never exercised and every file of a pack arrived under the
  first file's name.
- **S18 — a class fixed on one route and not its siblings.** When a class is fixed, enumerate every
  route to the same outcome (form, hand record, AI tool, worker, CLI, keyboard shortcut, context
  menu) and close each, or record why not. *e.g. (shop):* the 2026-10-07 classes "a refund tells the
  customer" and "every goods-back path needs a restock decision" were fixed on the card refund form;
  the hand-recorded refund and both AI refund tools did neither, and the 2026-10-08 audit found them
  again.
- **S14 — a fix the auditor may not make.** A finding in a file a project rule forbids editing is
  recorded with `path:line` and the exact change, under a "blocked by rule" heading the owner reads;
  never dropped as out of scope. e.g. two findings (a void legal sentence, a checkout total the
  customer never saw) sat in templates a project rule forbade editing.

### 2026-10-13 — the mixoweb legal-checkout build fix (/ecommerce-cia and /cia plus review-capped residue; three classes were made by the fix round itself, so the fixer's own edits are in scope)

- **S1 / S15 — a leg that silently substitutes a value it never stores.** Enumerate every two-leg
  flow (review/confirm, preview/apply, quote/accept, dry-run/execute) where one leg falls back
  without saying so: the leg that resolved must store or post what it resolved, one resolver serves
  both legs, and a test drives both legs with the stale value. *e.g. (shop):* the review page priced
  the session's delivery choice only while it was open and otherwise the first open option; the
  confirm re-validated the raw session value and refused "unavailable" on every Pay press. *Also:* a
  print or export preview that falls back to a default profile while the job is sent with the stale
  one.
- **S1 — a fingerprint that omits a fact the page shows.** A confirm fingerprint covers everything
  the person is agreeing to, split so the refusal names what moved instead of one catch-all
  sentence. *e.g. (shop):* the confirm hash covered prices and the delivery method but not the
  address, and two regions with different cancellation law cost the same, so a second tab moved the
  order under terms the buyer never saw — the fingerprint must cover address, region and terms
  edition, and the refusal name basket, details or price.
- **S13 — derive-don't-store has an exception: evidence of what was shown.** Before accepting
  "derive it", ask whether the source can change after the event the value attests; if it can,
  freeze the value (and the edition of the wording) at the event and make every later reader use
  the frozen column. *e.g. (shop):* the delivery region was computable from the address, but the
  address is editable after placement, so every later reader would apply the wrong regime. *Also:*
  the settings a render or print job was produced with, recomputed later from settings that have
  since changed.
- **S3 / S21 — a deny-list gate counted as a gate.** A safety gate is an allow-list (`=== 'local'`,
  or "live only on production"); the guard test refuses the deny-list form and has a case proving it
  does. e.g. an architecture test counted any mention of `APP_ENV` as a gate, so `=== 'production'`
  passed while `staging` with live keys booted with a default key, debug and the demo catalogue.
- **S13.1 — several readers of one configuration file.** One parser, public, called by every
  reader; a test feeds a commented and a quoted value to each reader. e.g. the web read `.env` with
  one parser, the cron dispatcher and the deploy preflight with two others that kept quotes and
  trailing `# comments`, so `APP_ENV=production # live host` was a different value per reader.
- **S20 / S22 — a refusal handed to the user and told to nobody.** A loop that refuses every attempt
  looks exactly like a quiet day when refusals go back to the user and nowhere else. Count refusals
  per reason per day (no personal data needed) and show a health row that is red for refusals the
  system causes and for loop-prone reasons past a floor. *e.g. (shop):* every refused checkout went
  back to the buyer and nowhere else. *Also:* an importer that rejects every file for a reason the
  code itself causes, shown only to the person importing.
- **S22 / S17 — text a rule requires inside a user-editable template.** Required text (law, licence,
  safety notice) placed as a placeholder in an editable template is dropped by any override written
  before the placeholder existed. Required text is appended by the renderer outside the editable
  copy, and a test renders it under an override. *e.g. (shop):* a notice the law requires on a
  durable medium, placed as a placeholder in an owner-editable mail.
- **S21 — a docblock stranded above the wrong function.** Inserting a method between a docblock and
  the function it described leaves two doc comments back to back: one now documents the wrong
  method, the other has none, and nothing fails. The fix round did it twice. Count back-to-back doc
  comments per file with the tokenizer and ratchet the count (shrink only).
- **S21 — the fixer's gate is the whole fast gate, before every commit.** Three fix commits broke
  checks the touched-file tests never ran (an AI-tool-graph allowlist, a static-analysis rule, an
  escaping assumption in an unrelated test). A fix commit runs the project's whole fast gate (suite,
  analyser, linter) first; "the new test is green" is not the gate.

### 2026-10-14 — the mixoweb Bootstrap → Tailwind/daisyUI move (each survived a green suite, clean analysers, screenshot diffs and an axe sweep)

- **S22 / S18 — a framework swap that keeps a class name and changes its meaning.** After any CSS
  or UI-framework swap, enumerate every component class the old and new framework share (`alert`,
  `card`, `btn`, `badge`, `menu`, `table`, `container`) and render each use: the same name is a new
  component until a rendered check reads its layout. e.g. daisyUI's `.alert` is a column grid where
  Bootstrap's was a block, so a notice with a heading, text and a button laid them side by side and
  made a 390px page 440px wide; every class ratchet saw "a class the framework draws".
- **S21 — a screenshot diff accepts a new width.** A page that grows sideways is a new picture, not
  a changed one, so the diff passed it. Measure `scrollWidth > clientWidth` at the narrowest width on
  every route and preview, with a written allow-list; an inline `max-width:400px` beside
  `max-w-full` is the commonest cause (the inline style wins).
- **S21 / S14 — an accessibility sweep that covers only the preview rows.** axe ran over fixtures,
  so a real route's icon-only link with `alt=""` and no name, and a banner's white text on pale
  amber, were never measured. Run it over the sitemap's real pages too; and know what axe skips:
  `::placeholder` contrast and symbol-only text are not checked at all, so a placeholder colour and
  a "×" need a rule of their own.
- **S21 — a contrast guard that reads classes and never the stylesheet.** The text-colour ratchet
  read the class names templates write; 74 `color:` declarations in the stylesheet itself (labels,
  notes, sale prices, ported legacy rules) were below AA, and three read `var()` of variables nothing
  defined (a fill that silently never drew). Measure every `color:` declaration against its own
  rule's background or the surfaces it can sit on, and refuse an undefined variable with no
  fallback.
- **S22.10 — a form reset that desynchronises the custom UI around it.** When a script resets a
  form, list every piece of UI state derived from its fields and kept outside the form; reset only
  the field that must go back. *e.g. (shop):* after a successful add, `form.reset()` put the variant
  radios back on the default while the swatch highlight and the hero image stayed on the pick, so
  the next add posted a SKU the screen did not show. *Also:* a tool-options form reset that leaves
  the viewport's gizmo and highlight on the old option.
- **S3 / S22 — a replaced library's quiet workarounds.** Before deleting a library, list what it did
  implicitly and re-prove each, on the browser that needed it. e.g. Bootstrap's bundle carried
  behaviour nobody wrote down: closing a menu when focus Tabs out, iOS Safari's tap delivery to
  document listeners (no-op `mouseover` on body's children), a disabled button while a request is in
  flight (Playwright WebKit with `has_touch` reproduces the iOS tap quirk: pointerdown and touchend
  fire, click does not).
- **S3 — a tokenizer that fails open at end of input.** Any scanner with an "open" state must throw
  or report when input ends with that state set; and an index heuristic (`[` before, `]` after) must
  not swallow array-literal elements. e.g. a reader that opened a `class="` region and never found
  its close swallowed every later literal and dropped the region at end of file, so the ratchet, the
  codemod and the CSS word list all lost every class after it with nothing said.
- **S16 / S22 — an asynchronous write whose failure changes nothing on screen.** Every client-side
  request needs a visible answer for each of: success, refusal, server error, no response. e.g. an
  HTMX add answered by an unmarked 500, a dropped connection or a timeout left the page as it was.
- **S21 — "only grows" stated and not enforced.** A list that must only grow carries a floor
  constant and names its must-have entries. e.g. a snapshot list said it never shrinks, and the
  check tied snapshots to the list, so removing an entry together with its files passed.
- **S20 — a record that an unrelated commit can delete.** A record other records cite needs a test
  that it is still there. e.g. a later task committed a working copy of the handoff written over an
  older version and dropped two tasks' lines, one of them the record another decision pointed at.

### 2026-10-16 — mixoweb, 2026-10-14..16: green on the laptop, red in CI, and nobody read the CI

These four are written out in full under their sweeps, where they are now part of the method:
**S19.3** environment parity (one engine, an all-privilege account and secrets always present are
the laptop's most permissive cell; name the production/CI matrix and require each cell RAN — report
line 2g); **S20.6** unread CI (a push is not done until its CI run is read; `not checked` is a
finding — report line 13) and CI as a budget (reproduce the cell locally, push rarely, never re-run
a red without a hypothesis); **S19.4** migration readiness (dump on A, restore on B, compare counts,
checksums and file hashes, smoke the app on B, write the lay procedure — report line 2h).

### 2026-10-22 — mixosupports, a React/three.js resin-support editor (non-commerce; each survived a green suite)

- **S22 / S21 — a filter tested only from the view the author used.** For every filter on a user
  gesture (facing, depth, distance, screen-space radius, visibility, layer), enumerate the views and
  states the person actually works from and test from at least two that differ, including the worst
  one; a filter whose pass rate depends on the camera or zoom is a mode the user cannot see (S22.6).
  e.g. a "Drag over" selection brush skipped support contacts whose surface normal faced away from
  the camera; overhang normals point down, so from any view above the build plate — the views the
  user works from — almost nothing qualified, and a stroke over plainly visible supports selected
  nothing. The filter had only been exercised from the view its author used. The fix moved the
  brush to screen space (a circle of N px against each support's projected body, with an occlusion
  ray against the model), as pure rules with unit tests shared by hover preview and paint.
- **S5 / S22 — the control's name promises a target the code does not hit.** For every gesture or
  control whose label names a target ("drag over X", "click X", "drop on X", "hover to inspect X"),
  check that the hit-test runs against the geometry or element the person sees and means, not a
  proxy the code finds convenient (an anchor point, a bounding-box centre, a hidden collider, a
  parent node); test by aiming at a visible part the proxy does not cover. e.g. "Drag over" matched
  a 3D sphere around the pointer's hit point against each support's contact tip on the model
  surface rather than the visible bodies (neck, pillar, foot) the user drags across, so dragging
  over a pillar hit points far from any tip and selected nothing while the user was plainly
  dragging over it.
- **S22 — a forced automatic state that disables the user's own toggle.** For every automatic state
  (a mode forced by a threshold, a performance fallback, a safe mode, a read-only lock), the user's
  control stays operable and wins, or the screen says why it is locked and what ends it; a forced
  state the person cannot leave is the screen storey's "one no person can dismiss". e.g. when the
  camera went below the build plate the view forced "Tips only" on and disabled its button, so
  after Bottom view (and Fit view, which keeps that angle) the user could not turn tips off. The
  fix shape is general: the automatic state turns on by itself, the control is never disabled and
  a click flips it, and crossing the threshold again hands the choice back to the automation.
- **S1 / S18 — a region rule checked at one end of an entity that touches the region at another.**
  For every rule of the form "nothing in region R" (exclusion zones, keep-out areas, clip volumes,
  forbidden ranges, permission scopes over intervals), enumerate every point where the entity
  touches or crosses the guarded region — both ends, the path between, every child — and test each;
  one end checked is a sample (S18). e.g. a painted no-support zone removed automatic supports
  whose top contact sat in it, but a column from an upper overhang that landed on the painted lower
  surface stayed, because only the top contact was tested. The fix tested the landing point too,
  with the builder's own landing ray, in the one function the main thread and the mesh worker
  share — so counts, checks and the built mesh agree.

### 2026-10-22 — mixoweb pre-launch audits (/cia and /ecommerce-cia ahead of a host move)

- **S20 — a watchdog that answers before the code it guards runs.** The outermost check must
  exercise the path a real request takes — boot the application, read the store through its own
  layer, render one real page — or it proves only that the web server and the database are up.
  Enumerate every health, status and uptime endpoint and say where in the request path each one
  returns; one that returns before the application boots is a liveness answer to a readiness
  question (S20.4). Then name what reads the application's error log: a log nothing alerts on is
  the report storey. e.g. (shop) a `/status` endpoint answered `SELECT 1` before the framework
  booted and stayed 200 while every storefront page was 500; the uptime probe pointed at it would
  have stayed green through the outage, and the PHP error log recording every 500 fed no alert.
- **S20 / S3 — required configuration missing, and the job exits 0.** A worker whose required
  configuration is unset, or present and undecryptable, must in production exit non-zero, leave its
  heartbeat stale or marked degraded, and turn its health row red; "nothing to do" and "cannot do
  anything" are different states (step 2's blind case, applied to advancers per S20.1). Enumerate
  every worker's config guard and read what it returns. e.g. (shop) the mail workers returned 0
  when SMTP was unset or its stored secret would not decrypt, so the heartbeats stayed fresh and the
  mail health row showed green beside "last sent: never".
- **S21 — a path filter matched against the absolute path.** Every test that includes or excludes
  files by path (an orphan-class scan, an "every X has a test" pairing, a forbidden-call grep, an
  allow-list) matches against the path relative to the repo root, never the absolute one, or the
  checkout's location changes the verdict. Prove it from a checkout whose parent folders carry the
  excluded names. e.g. an orphan-class test skipped any absolute path containing `/scratchpad/`,
  `/docs/` or `/tests/`, so a checkout under such a folder failed for no reason or — worse — skipped
  every file and passed vacuously.
- **S2 / S15 — a second sign-in method linked to an existing account by email.** When an OAuth,
  magic-link or SSO sign-in attaches to an existing account because the address matches, and the
  account's creator never proved that address, the link must remove the creator's password and end
  their sessions; otherwise a stranger who pre-registered the victim's address keeps a way into the
  account the victim now uses — verified by the victim's own sign-in — and everything it
  accumulates (pre-hijack takeover). Enumerate every path that attaches an identity to an account
  and compare each with the password-reset path, which already treats "proved the inbox" as the
  event that ends earlier credentials; asymmetry between the two is the signal. e.g. (shop) a
  Google sign-in linked by email kept the unverified account's password, so the pre-registrant
  could sign in later and read the buyer's orders and download history.
- **S19.4 / S10 — a dev-machine override retargets "the old host".** A hosts-file entry, DNS
  override, SSH alias or proxy on the machine driving a host move silently points steps meant for
  the old host at the new one (or the reverse), and a backup, final export or "still works" check
  then succeeds against the wrong side. A move runbook says, per step, which host it runs against
  and how to confirm it (IP, server hostname, a marker file), and when each override is switched
  on and off. e.g. the owner's laptop already mapped the shop's domain to the new server, so every
  "on the old host" step would have reached the new one.
- **S19.4 / S16 — the move window.** An external writer (webhook, callback, queue consumer) still
  delivering to the old host after the dump is lost unless the runbook stops it or re-queries and
  replays it after cutover, and a closed-for-the-move gate must still pass the token-addressed pages
  people were sent links to. The payment form of this is in `ecommerce-cia` (2026-10-22 classes).

### 2026-10-22 (later) — runtime audit of refunds, payments, downloads and settings, and the live proof of its fixes (each survived a green suite and earlier static audits; found by driving the running application)

- **S5 / S22 / S15 — mutual refusal: two controls for one job, each pointing at the other.** When a
  routing rule ("this kind goes through the automated path, that kind by hand") is copied into each
  surface that offers the job, the copies drift, and an item lands where the automated form says
  "use the manual one" and the manual form says "use the automated one" — nobody can do the job.
  Enumerate every job with two or more entry points (automated and manual, admin and operator tool,
  desk and CLI). The rule must live in one table keyed by every dimension that decides it; every
  surface, guard and executor reads that table; an unknown key is refused by all of them. Then walk
  each value of the key through each surface and read what it says; two surfaces that each end in a
  refusal are the finding. e.g. (shop) the refund form asked one gateway's rule about every gateway,
  and the hand form refused what the router told the operator to enter by hand: a paid card order
  had no refund route at all.
- **S18 / S4 — a capability assumed per provider, not per kind of item.** A provider's API
  rarely supports an operation for every kind of thing it handles. Key the capability by
  (provider, kind) from the provider's own document, and enumerate the kinds a provider accepts
  against the operations offered. e.g. (shop) a card-refund API offered for ATM transfers,
  convenience-store codes and wallets of the same gateway.
- **S12 / S2 — an idempotency key that never changes after a failure.** The twin of the key that
  names the payload: a key built from (entity, amount) alone makes a declined or failed attempt the
  answer to every later attempt, so retry is impossible and the operator is told the old failure
  forever. The key carries the attempt: it advances only when every earlier attempt is known to have
  failed, and stays put while one is pending or succeeded. Probe: fail the operation once, fix the
  cause, retry, and read what the second press does.
- **S15 / S1 — a terminal state tested as one number.** "Fully done" computed as `this amount ==
  total` misses the case where several partial amounts add up to the total, and the thing stays
  actionable (shippable, refundable again). Terminal checks compare the sum of everything applied
  against the total, from the same source every other reader uses. Probe: apply the parts one at a
  time and read the state after the last.
- **S5 / S22 — a message written through one accessor and read through another.** A flash message,
  session value or one-shot flag stored through the framework's session API and read from the raw
  superglobal (or the reverse) never shows, and nothing errors. A one-shot "sent" or "done" flag
  that is not cleared when the send fails blocks every resend. Enumerate every read and write of
  each session key and assert one accessor; for each one-shot flag, name the event that clears it
  and walk the failure path.
- **S13.1 / S20 — a hand-maintained list of what to watch or run, beside the catalogue of what
  exists.** A watched-jobs list or a fallback scheduler's job list written by hand drifts from the
  job catalogue, and the critical job added last is neither watched nor run when the primary
  scheduler is gone. Derive the list from the catalogue, or add a parity test that fails when a
  catalogued job is in neither the list nor an explicit exemption. Enumerate every second list that
  restates the catalogue.
- **S16 / S20 — a stored status that no consumer drains.** A row stored as "pending" that nothing
  will ever process counts as stuck forever in health and is skipped by retention sweeps, so it
  grows and alarms for ever. A status says what will happen to the row: for every status value name
  the process that moves it on; a value with no such process is a terminal one, named so.
- **S20 / S2 — an alarm upserted on a key that omits a distinguishing dimension.** An `ON
  DUPLICATE KEY` or upsert for alarms whose unique key lacks a dimension that tells two alarms apart
  (provider, source, kind) collapses two different alarms into one row carrying the first's label
  and the second's text, and one alarm is lost. For every alarm upsert, list the dimensions the key
  carries and the dimensions the message mentions; a dimension in the message and not in the key is
  the finding. Probe: raise two alarms that differ only in that dimension, with equal counts.
- **S22 — a system or sentinel row shown in a user-facing list under the wrong framing.** A row the
  system files about itself (a check "could not finish") has no subject of the kind the list is
  about, so a list that selects "open rows whose subject is missing" presents it as the alarming
  thing ("money received for an order that does not exist"), with the raw sentinel as its
  identifier. Enumerate every sentinel id and every list that reads the table; each list excludes
  the sentinels or gives them a panel of their own with their own words and action.
- **S21 — a teardown that restores saved state after a skipped setup.** A `tearDown` that puts back
  what `setUp` saved writes null (or an empty default) over live process-wide state when `setUp`
  returned early or was skipped, and every later test in the process runs against it. Teardown
  returns early when setup did not complete; grep each teardown that restores a global, cache or
  snapshot.
- **S20.5 / S21 — prove the fixes live after they merge.** These classes were found by driving the
  running application against real data (the live admin pages, real rows) after a round of fixes
  had merged, not by the suites, and several were interactions between two fixes that each passed
  alone. Keep the post-merge live walk mandatory: boot the merged tree, open the pages the fixes
  touch, read the rows they wrote, and report the result as its own line.

---

**Reading receipt: _the channel is the finding_.** Quote this phrase on the Step 6 receipts line to show this
file was read rather than inferred from the skill's index. It appears nowhere else.
