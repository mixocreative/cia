# Fixture runs

| Date | Skill commit | Runtime | Tier | Hits | Near | Miss | False+ | Minutes | Note |
|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | no run recorded yet; first run establishes the baseline |
| 2026-09-15 | 5b5186d + the external-lessons edits (browser-walks.md, S2.1, S16.2, S19.1, S20.2, doctrine §8.1–8.2) uncommitted | Claude (subagent, cold) | Screen — `pre-launch audit, Screen tier` on fixture-service | 6 | 4 (S2 HIGH vs CRITICAL; S3, S22, S21-vacuous MEDIUM vs HIGH) | 0 | 0 | 10 | **First baseline.** All 10 planted sites found with path:line and a quoted line; both controls verified; commerce detection none; 4 extra true findings (finish() without a status predicate, untyped config → job stranded running, S19 no host, heartbeat partial write). Every near is a grade one level low on a money/safety path — the severity floor added to reporting.md the same day. 185k tokens. |
| 2026-09-17 | a189d97 (S12.2, S15.3–S16.4, S19.2, S20.4, S22.8, S23.2, kitchen-sink, README objections) | Claude (subagent, cold, key excluded) | Screen — `pre-launch audit, Screen tier` on fixture-service | 8 | 2 (S2 HIGH vs CRITICAL; S21-vacuous MEDIUM vs HIGH) | 0 | 0 | 8 | **Up from 6/4.** S3 fail-open, S22 unrendered and S21 contamination now at the floor grade; S20 blind + dead watchdog filed as one finding citing both sites; both controls verified; 6 extra true findings (Retry route absent, config schema, no retry delay, S19 four unknowns, four untested state writers, blank empty row). 177k tokens. |
| 2026-09-19 | a189d97 + today's edits uncommitted (walk step (f) layout geometry; reporting.md severity floor rewritten around the *primary path* instead of "money path"; S2, S3 grading paragraphs added; S20 unread-heartbeat sharpened; answer key moved out of the fixture to `tests/EXPECTED-fixture-service.md`) | Claude (subagent, cold, key outside the fixture; one `git status --porcelain` on the fixture printed two path names, no content) | Screen — `pre-launch audit, Screen tier` on fixture-service | 10 | 0 | 0 | 0 | 9 | **Up from 8/2 — first 10/10.** The two standing nears (S2 HIGH vs CRITICAL, S21-vacuous MEDIUM vs HIGH) closed by the grading text, not by the auditor: three earlier runs today measured the old text at 8/2 (one) and 7/3 (one, key-guarded but pre-edit) and were not recorded as gate rows. Two of the three runs before the key move leaked the answer key through the S6 deferred-work grep the doctrine prescribes over `tests/` — the key now sits beside this file. 4 extra true findings (config typing, retry-everything, five S19 unknowns, two untested state writers); 187k tokens. |
| 2026-09-20 | c144504 + today's edits uncommitted (S5.1 retired-caller script; S13.1 second hand-rolled map; S20.5 walk receipt is a one-day fact; S21 shape 6 runner's file listing; S22.9 button with no handler) | Claude **Sonnet** (subagent, cold, key outside the fixture, git forbidden) | Screen — `pre-launch audit, Screen tier` on fixture-service | 6 | 1 (S21-contamination LOW vs MEDIUM) | 3 (S3 fail-open catch accepted on an inline comment; S20 dead heartbeat left as step prose, never graded; S21 assert-empty vacuous pass not checked) | 0 | 25 | **Signal row, not the gate row — first run on a cheaper auditor model; the row below re-runs the same doctrine on Opus.** Every miss is a promotion/threshold failure (site found, finding not filed), not a discovery failure. Lesson: RUNS rows now name the model; the gate compares like with like. |
| 2026-09-20 | c144504 + the same uncommitted edits | Claude **Opus** (subagent, cold, key outside the fixture, git forbidden; prompt adds "every threshold-meeting observation becomes a graded finding") | Screen — `pre-launch audit, Screen tier` on fixture-service | 10 | 0 | 0 | 0 | 12 | **Holds the 10/10 baseline** after five additive doctrine edits; 9 extra correctly-evidenced findings beyond the planted rows (D2 stuck orphan, two more S22 states, S11/S19/S24/S3/S12 sites) — candidates for new planted rows, none a false call; both controls kept out of the findings. |
| 2026-09-24 | 92fe7e5 + this session's edits uncommitted (promotion rule, evidence ledger §11a, browser-walks §§12–14 + the stack mapping, tier runtime column, S2/S15 runtime twins, fixture-aware gate) | Claude **Opus** (subagent, cold, key outside the fixture) | Screen — `pre-launch audit, Screen tier` on **fixture-service** | 10 | 0 | 0 | 0 | 40 | **Holds the 10/10 baseline across the largest doctrine change this harness has seen**, and the new half is exercised: 4 state-delta ladders, 7 of 9 adversarial rows (the 2 skipped are N/A with reasons — *operator edit mid-flight* could not run **because no operator write path exists**, which the run filed as a finding rather than a gap in the walk), and the S2 probe **fired 10 trials × 2 OS processes: both claimed the job 10 of 10 times**, so the TOCTOU is CONFIRMED rather than predicted — plus a control probe at `enqueue` proving the mechanism missing at `:57` exists at `:44`. The ledger used **PARTIAL**, added the same day from the commerce fixture's lesson, and every PASS row named what its artefact covered and what it did not. 6 extra true findings (out-of-order `finish` reopening a `done` job — confirmed at runtime; unvalidated config types; no `busy_timeout`; `finished_at` NULL on the failure path; no deploy artefact; a config snapshot diverging from the monitor's live re-read). It declined to run `score.py` because that reads its own answer key. 215k tokens. |
| 2026-09-24 | 50b21d8 + the precision controls and Stripe/corpus work uncommitted | Claude **Sonnet** (subagent, cold, key outside the fixture) | Screen — `pre-launch audit, Screen tier` on **fixture-service** | 8 | 2 (defect 4's blind-instrument site folded into FS-04 rather than named; defect 10 graded LOW against a MEDIUM floor) | 0 | 0 | 70 | **The cheap-model gate, and the reason the promotion rule exists.** On 2026-09-20 the same fixture scored Opus 10 / Sonnet 6 on identical doctrine, every Sonnet miss a promotion failure. With the promotion rule in `reporting.md` instead of the harness prompt, Sonnet scores **9.0 against Opus's 10 — the gap closed from 4 to 1**. It fired the §13 probe (two threads, one job, **both workers won**), ran 2 ladders plus 3 adversarial probes, and used the §13 disproved-reading rule unprompted: *"I expected sqlite's locking might mask the race — it did not. Stated, not filed as a finding, since it was a reading that turned out wrong."* **All eight controls verified, including all five precision controls added the same day — 0 false positives**, and VC-3 was explicitly contrasted against the fail-open it is built to resemble. 3 extra true findings, one of which (FS-06) is a real defect this harness had acquired by accident; it is now key row 11. 232k tokens. |

## Runtime evidence, per run (2026-09-24 onward)

The table above scores what the auditor **found**. This one scores what it **ran** — the half
of §0.6 the harness could not previously see. A run recorded above with no row here was a code
review; say so rather than leaving the reader to assume.

| Date | Fixture | Ladders | Adversarial rows | Probes | Ledger rows P / F / U | PASS without artefact | Note |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | no runtime-scored run yet; the first one establishes the baseline |
| 2026-09-24 | fixture-service | 4 | 7 of 9 (2 N/A, each with its reason) | 2 (`claim_batch`, 10 trials; plus a control probe at `enqueue`) | 3 / 7 / 2 (+4 PARTIAL) | 0 | First runtime-scored run on this harness. No HTTP surface exists here, so the walk was the scripted equivalent §0.6 Step 4 names — 12 scenarios across 4 modules, 7 artefacts — and routes/assets are N/A on the map rather than a skip. The run also recorded **two of its own readings that the runtime disproved**, which is now doctrine (`browser-walks.md` §13). |

**`PASS without artefact` is the column that matters most.** It counts ledger rows the run
marked PASS while citing no artefact produced in that run. The honest value is **0**, at every
tier, forever: a non-zero number means the auditor promoted a capability from reading, which is
the one thing `reporting.md`'s ledger forbids. It is scored as a false positive.

## Corpus — ground truth nobody planted (2026-09-24 onward)

Real repositories, audited at the commit **before** a maintainer's own fix commit. The oracle is
that commit's diff, not anybody's reading of the code. `tests/corpus/README.md` holds the rules;
`tests/corpus/entries/` holds the entries and **the auditor never reads either**.

This is the only table here whose number cannot be improved by knowing the answer key, because
there is no answer key — there is a stranger's bug fix. It is also, today, nearly empty, and an
empty corpus proves nothing.

| Date | Entry | Verdict | Runtime | Note |
|---|---|---|---|---|
| 2026-09-24 | connection-leak-python | **HIT** | Claude **Sonnet** (subagent, cold) | `Theepak966/TorroMainRepo` at the parent of `7688e1c6` *"Fix: Critical database connection leak and bare except clauses"*. **(1) The leak:** F1 CRITICAL located `thread_db = SessionLocal()` at `main.py:1997` inside a 215-line `try` with no `finally`, then did what the oracle did not think to ask for — it enumerated the **exit paths individually**: the `return None` at :2091 drops the session, the "created" branch returns it in a dict the consumer never reads at :2326, and only the "updated" branch closes it at :2322, *three lines above the one that does not*. **(2) The bare excepts:** F4 HIGH found `except: pass` in `asset_deduplication.py:109-110` — a file the maintainer's commit also touched — and then closed the loop between the two halves: when the pool is exhausted by (1), the dedup fallback fails on the same broken session, is swallowed by (2), returns `None`, and every blob is routed down the **leaking** branch. Pool pressure feeding pool pressure, with no log line. It also filed two unplanted CRITICALs, one of which is an `UnboundLocalError` that makes the *default* discovery path dead on every call — so the two bugs partition the function's input space: one shape leaks, the other never runs. 224k tokens. |
| 2026-09-24 | basket-idor-nestjs | **HIT** | Claude **Sonnet** (subagent, cold) | `mishadanilovich/coffee-shop-server` at the parent of `6ebc7bfc` *"Fix basket IDOR and link Stripe payments to orders via webhook"*. The maintainer threaded a `@UserId()` through four handlers; the audit named **all four** — F2 CRITICAL on `findById` (*"returns any basket by id with no ownership check"*), F3 CRITICAL on add and remove (*"neither handler even injects `@UserId()`, so there is no server-held identity to check against"*), F1 CRITICAL on submit — and proposed the same remedy. It went further in two ways the oracle does not require: it noticed `remove()` three methods away **already scopes by `{ id, userId }`**, making the gap an intra-file inconsistency rather than an unknown technique, and it followed the unscoped `findById` across a module boundary into `stripe.controller.ts`, where the same id lets anyone raise a PaymentIntent against a basket that is not theirs. A **new class for this table** — object-level authorization, not a race and not an idempotency gap. 143k tokens. |
| 2026-09-24 | inventory-orphan-table-ts | **PARTIAL** | Claude **Sonnet** (subagent, cold) | The hard entry, chosen against this table's selection bias: its commit title names symptoms and its primary defect is an **absence**. Two declared halves. **The lock — clean hit:** F1 CRITICAL / S2 at `lib/redis-lock.ts` and `lib/storage/cloudflare-kv.ts:93-102`, showing the primitive documented as atomic is a read-modify-write on the backend `resolveStorageProvider()` picks *by default*, so *"two concurrent `hincrby` calls on the lock key both read 0, both compute 1, both believe they hold the lock"* — proved by quoting the storage adapters' own CONCURRENCY CAVEATS against the lock's own atomicity claim, which is S4 played against a codebase's internal documentation rather than a vendor's. **The absent writer — partial:** F4 HIGH reached `inventory_levels` from the other end, showing the admin matrix renders Out/Low/OK badges from a table kept current only behind a flag that is off by default; it did not reach the consequence the oracle names, that `decrementInventory` fails *closed* on the missing row, so gating checkout on it would refuse every purchase. It also filed F2 CRITICAL, unplanted and worse than either: the direct-checkout route **charges the card before the lock is taken at all**, so a perfect lock would not save it. And F5 records a doc comment that nearly misled the audit into filing a live module as dead — caught by grep, declared rather than buried. 169k tokens. |
| 2026-09-24 | license-race-ruby | **HIT** | Claude **Sonnet** (subagent, cold) | `floorballdeutschland/saisonmanager-api` at the parent of `30c8d076` *"fix: Race Condition bei Lizenzantrag absichern"*. Filed **F7 / S2** at `players_controller.rb:124-152`, quoting `player.licenses.map! do |lic|` and naming the mechanism exactly: *"read-JSONB-column → mutate in Ruby → save-whole-record, with zero row locking anywhere in the codebase"*, with the grep that proves the absence. Graded MEDIUM where the maintainer thought it worth a dedicated commit — the entry set no minimum, so it scores as a hit, but the grade is on the low side for a lost update on the record a licence lives in. **Its best finding was not the planted one**: F1 CRITICAL, a Ruby truthiness bug where `ph[:vm].intersection([...]) || …` returns a truthy empty array, turning "deny unless your club is playing" into "allow any club manager" across ten of twelve write actions — and it **confirmed it by running `ruby -e`** rather than reasoning about it, which is S10 applied without being asked. 179k tokens. |
| 2026-09-24 | fail-open-startup-java | **MISS** | Claude **Sonnet** (subagent, cold) | `WilliamAGH/findmybook` at the parent of `99a838f1` *"fix: stop swallowing exceptions in startup config normalization"*. The defect: a `.env` loader that caught `IOException | SecurityException`, wrote `log.debug("Skipping .env file loading")` and continued on defaults; the maintainer's fix throws. The run audited that exact file, filed **FMB-06 MEDIUM / S3** — a *different* fail-open two hundred lines away — and walked past this one. By this entry's own rule (*"naming the file for a different catch does not count"*) that is a miss, and it is **the most useful row in this table**: the cause is a doctrine gap, not a model failure. The catch **logs**. S3 graded fail-open by posture and never said what a log level does to the report, so a line at DEBUG read as "handled" to a sweep looking for silence. Nobody runs production at debug. S3 in both skills now grades the level: *debug/trace is silence with a receipt*, and the author's own `// Silently continue` comment is the author agreeing with the finding. 237k tokens. **Also the first run to print reference receipts unprompted** — sweeps.md, doctrine.md and reporting.md quoted, `browser-walks.md` correctly absent because it ran no walk, which is the canary behaving exactly as designed. |
| 2026-09-24 | webhook-idempotency-go | **HIT** | Claude **Sonnet** (subagent, cold) | `Veda50/Go-Commerce-API` at the parent of `ac18fb33` *"fix: idempotency check on duplicate Xendit webhook"*. Filed **F3 CRITICAL / S23** at `internal/service/order_service.go:121-123`: *"an unconditional status write with no current-state guard and no persisted webhook/event-id ledger — nothing distinguishes a first delivery of a PAID callback from a replayed or out-of-order one"*, quoting the function the maintainer rewrote. Also filed the missing `RowsAffected` check beside it, which is the silent no-op the same function hides. 8 further true findings. 121k tokens. |
| 2026-09-24 | webhook-idempotency-stripe-ts | **HIT** | Claude **Sonnet** (subagent, cold) | `Stefiro777/alata-investment-club` at the parent of `5b9ee911` *"fix: idempotency check on stripe webhook to prevent duplicate emails"*. Filed **STRIPE-01 CRITICAL / S23** at `app/api/stripe/webhook/route.ts:170-278`: *"never reads `event.id`, never checks whether this payment intent has already been processed … every re-delivery double-inserts the finance ledger row and re-sends both emails"* — the duplicate e-mail is the maintainer's own commit subject. It also checked `middleware.ts` to confirm the raw body was not at risk, which is §3 of the Stripe guide applied without being told to. 6 further true findings. 125k tokens. |
| 2026-09-24 | inventory-race-resolution | **HIT** | Claude Opus (subagent, cold, oracle unreachable) | `hackclub/resolution` at `bfa769c2`, the parent of `684a14bf` *"fix: race condition on inventory — use atomic WHERE guard on stock decrement"*. The run filed **WH-001 CRITICAL / S2** at `orders/new/+page.server.ts:123`, quoting the two lines the maintainer changed, and named the second touched file (`batches/+page.server.ts:291`) as an S2 site in the same sweep. Its proposed fix — `.where(and(eq(id, …), gte(quantity, item.quantity)))` plus an affected-row check — is **the maintainer's actual diff, character for character**. 14 further findings on real code, including a CRITICAL it found *outside* the named scope (`warehouse-backend`'s actions authorise nothing, and SvelteKit runs actions before loads) and reported rather than suppressed. It opened by declaring itself a **code review, not a Screen** because no runtime walk was in budget, and every one of its 15 ledger rows is UNVERIFIED as a result — which is the doctrine's own rule applied to itself, unprompted. 237k tokens. |

**Class coverage, stated so the hit rate can be read properly.** The entries now span six classes
— select-then-act (S2), webhook idempotency (S23), fail-open (S3), orphan capability (S13),
object-level authorization, and resource lifecycle (S12) — across seven languages: Go, TypeScript,
Ruby, Java, Python, SvelteKit and NestJS. Early in this table the first three entries were all
variations on "no idempotency guard", which is a narrower instrument than the number of rows
suggested.

**On selection bias, before the hit rate is read as a claim.** Every entry above was found by
searching commit messages for the defect, so each oracle's commit *names* what it fixed. That is
a real bias and it flatters the instrument: a maintainer who writes "fix: race condition on
inventory" has already done part of the auditor's work, even though the auditor never sees the
message. The `inventory-orphan-table-ts` entry was added to push against it — its commit title
names symptoms rather than a class, and its primary defect is an **absence** (a table nothing
writes, feeding a gate that fails closed) rather than a wrong line. The honest read of this table
is: strong on named defect classes in unseen code, and still unproven on defects nobody has
already characterised.

**The receipts found a packaging failure on their first day.** Two of the six cold runs this
session — one on the commerce fixture, one on the Ruby corpus entry — worked from `SKILL.md`
alone and never opened `references/`. Both said so in their reports, in the receipts line,
because the line exists now. Before it, a run like that was indistinguishable from a run where
the doctrine simply did not cover the defect, and the wrong thing would have been fixed. The
Ruby run put it plainly: *"Reference receipts: not claimed — this run read SKILL.md only; the
references/*.md files were not opened, so sweep numbering below is applied from the SKILL.md
index, not the full doctrine text."* That is a good report of a bad run, and it is worth more
than a confident one.

**A corpus with no misses is a corpus that is too easy.** The first miss arrived on the fourth entry and paid for the whole harness: it found a hole in S3 that four fixture runs, two models and three earlier corpus hits had all walked past, because no fixture had ever planted a failure that *logs at the wrong level*. That is what this table is for. A hit rate that never moves is a warning, not a result.

**One entry is one data point.** This row is the strongest evidence in the harness — ground truth
authored by a stranger, found before the fix, with the identical remedy — and it is still a
single entry on a single defect class (S2) in a single language. The number to watch is whether
the hit rate holds as entries are added by somebody not choosing them to flatter the instrument.

## Blind-forward — findings the project itself later confirmed (2026-09-24 onward)

No oracle existed when these audits ran: the snapshot is a commit part-way along a real
repository's history and the auditor is forbidden from looking forward. `forward.py confirm`
replays what the maintainers did next. `OPEN` is an honest verdict here, not a gap.

| Date | Repo @ snapshot | Finding | Verdict | What the project did next |
|---|---|---|---|---|
| 2026-09-24 | `hackclub/resolution` @ `cc63253a` (51 first-parent commits before the tip) | RES-001/002 CRITICAL+HIGH — `onDelete: 'cascade'` from `user` through `workshop` reaches the `ambassadorPayout` ledger and *other* participants' completion and ship records, with no soft delete and no confirmation, from one admin click | **OPEN** — and independently verified | 51 later commits, one of them *"fix: address PR #12 review — migrations, authz, billing, SSRF, validation"*, touched `schema.ts` and **changed no cascade rule**. The chain is still there: `grep` at the snapshot confirms `authorId` cascade at `:61` and the workshop→completion cascade at `:75`–`:76`, exactly as named. Nobody has collected this defect; it is not fixed because nobody has looked. |
| 2026-09-24 | same snapshot | RES-006 — `validateFormData` coerces any numeric-looking form field to a number before Zod sees it, and has no caller | **OPEN** — independently verified | `grep -rn validateFormData src/` returns **one** line: its own definition. Dead today, a landmine the day it is wired to a route, exactly as the finding says. |
| 2026-09-24 | same snapshot | RES-008 HIGH — the test hand-copies `computeStartingWeek` from the production module instead of importing it, so the suite proves the copy | **OPEN** — independently verified | `computeStartingWeek` is defined **twice**: `enrollmentService.ts:10` and `enrollmentService.test.ts:5`. A green run there is evidence about the copy. |
| 2026-09-24 | same snapshot | RES-003 HIGH — `enrollParticipant` finds-then-inserts with no unique-violation handling, so a double-tab OAuth callback races the index | **OPEN** — independently verified | The `findFirst` → branch → insert shape is at `enrollmentService.ts:38-52` as described; the file has had **no later commit at all**. |

**What this first blind-forward run does and does not show, stated before the number can be
misread.** It produced **8 findings on code no oracle existed for**, and of the four spot-checked
mechanically at the snapshot, **all four claims are exactly true** — the cascade chain, the
orphan function with one occurrence in the whole tree, the hand-copied test helper, the
find-then-insert. **Zero were WRONG.** But **zero are CONFIRMED-BY-FUTURE either**, because the
project has not touched three of the four files in 51 commits, and the one commit that did touch
`schema.ts` changed no cascade rule.

So the honest reading is: *this mode can produce verifiable findings on unseen code with no
oracle, and it has not yet caught a maintainer agreeing.* `OPEN` is the mode's most common
verdict by design — an audit that only scores when a project later fixes something is an audit
that scores slowest on the projects that need it most — but a table of nothing but `OPEN` proves
less than one `CONFIRMED-BY-FUTURE` would. That row is the next thing this harness needs, and it
needs a repository whose maintainers are still actively fixing the files audited.

## Cost — what a run actually takes (2026-09-24 onward)

An instrument nobody can afford to run is not an instrument. The tier table promises budgets;
this records what was spent, so the promise is checkable and so the sweeps can eventually be
ordered by measured yield rather than by tradition.

| Date | Fixture / target | Tier | Tokens | Minutes | Findings | Tokens per finding | Time to first CRITICAL |
|---|---|---|---|---|---|---|---|
| 2026-09-24 | blind-forward: hackclub/resolution | code review (no runtime) | 231k | 11 | 8 | ~29k | first line of the report |
| 2026-09-24 | corpus: hackclub/resolution | code review (walk out of budget) | 237k | 8 | 15 | ~16k | first line of the report |
| 2026-09-24 | corpus: Veda50/Go-Commerce-API | code review (walk out of budget) | 121k | 3 | 9 | ~13k | first line of the report |
| 2026-09-24 | corpus: Stefiro777/alata (Stripe) | code review (walk out of budget) | 125k | 3 | 7 | ~18k | first line of the report |
| 2026-09-24 | corpus: coffee-shop-server (IDOR) | code review | 143k | 4 | 8 | ~18k | ranked first |
| 2026-09-24 | corpus: TorroMainRepo (leak) | code review | 224k | 7 | 9 | ~25k | ranked first |
| 2026-09-24 | fixture-service | Screen | 215k | 40 | 16 | ~13k | spoken first, before the report (the run put three CRITICAL/HIGH findings in its opening lines per §0.11) |
| 2026-09-24 | fixture-service | Screen | 232k | 70 | 13 | ~18k | spoken first, in the owner paragraph (sonnet) |
