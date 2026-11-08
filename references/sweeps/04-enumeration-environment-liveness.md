# Sweeps S18–S21 — exhaustive enumeration, environment constraints, safety-net liveness, the suite as instrument

> Part of `references/sweeps/` (index: `README.md`). Split from the former `sweeps.md` on 2026-11-09 - text unchanged. Read every file in the folder per §0.9.

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

- **A document generated from an authority needs a test that it is still generated, or it is a
  document that was true once (2026-09-24, proved).** The direction here is the inverse of the rest
  of this sweep: the artefact is *derived* from the source of truth rather than checked against an
  external one, which makes people trust it more and check it less. An environment reference
  generated from `.env.example` had drifted from it; the guard that caught it **regenerates and
  compares**, which is the only form that works — a reviewer reading both files side by side is the
  thing that already failed. The sibling shape is the same rule pointed the other way: a new
  environment variable read by the code but absent from `.env.example`, caught by a test that pins
  the two sets together. **For every generated or mirrored artefact — a reference document, a
  schema dump, a fixture, an example config, a client stub, a type definition — name the test that
  regenerates it and fails on a difference, or record that there is none.** Enumerate them the way
  this sweep enumerates anything else: the population is "everything in the repository that was
  produced from something else in the repository", and a member with no currency test is a cell
  marked unverified, not a document.

- **The rule under all of these: derive the set, or pin it — never restate it.** Four separate
  findings on 2026-09-24 were one defect. A test hand-copied four of nine configured hosts and
  stopped matching when the set grew (S21 shape 10). A generated reference drifted from its
  generator. An environment variable existed in code and not in the example file. And — the
  instance that settles what the rule should say — **this skill added a verdict to its evidence
  ledger and left two other places in its own `SKILL.md` enumerating the old three**, within an
  hour of writing shape 10 down, on the smallest possible surface, by the author most primed to
  avoid it. That is not carelessness in any of the four. **An enumeration repeated in three places
  has no single source of truth by construction**, so the rule cannot be "check your enumerations"
  — checking is what failed. Either the set is *derived* at use (read the config, reflect over the
  enum, regenerate and compare) or it is *pinned* (one canonical list, and every other mention
  points at it rather than repeating it). Prose can pin as easily as code can; what neither can do
  is restate and stay correct. When enumerating for this sweep, count the **places** a set is
  written, not only its members — a set written once is a fact, and a set written three times is
  three facts that will disagree.



Report line format: `S18 — subject, authority cited; N cells enumerated, M verified against the document, U unverified; matrix in the report. Re-walks triggered by findings this run: K.`

**When the authorities disagree (2026-10-12).** Manual, validator, sandbox and FAQ will sometimes say
different things about the same cell. Record a contradiction row (`evidence.md` §E7) with both quotes and
their authority, block only that cell's obligations, and keep enumerating — a higher authority wins only
inside its own scope, so the sandbox's answer does not close the production claim.

## S19 — Environment-constraint reconciliation. A REQUIREMENT THE HOST MUST SATISFY, NEVER CHECKED AGAINST THE HOST THAT WAS CHOSEN

The owner's question: *"does [this] also need whitelist IP…? If so our shared hosting launch won't make it."* Both facts were already written down. **In the same document.** The provider's requirement was in the deploy prerequisites; the chosen host was in the section above it. Nobody multiplied them.

This is not S17 (a control whose enforcement is elsewhere) and not S18 (sampling where enumeration was needed). It is narrower and more embarrassing: **two known facts, never crossed.**

**The mechanism that hides it, and it is worth stating because it is almost universal:** the requirement had been written as *a task for a human*. "Register the outbound IP with the provider" became a tidy row in a deploy checklist — and **the moment a requirement becomes a checklist item, it leaves the audit's scope.** Nobody asks whether the task is *possible* on the target; they only track whether it is *done*. A constraint converted into a chore is a constraint nobody validates.

Method:

1. **Extract every environment precondition your dependencies impose.** Read them out of the integration manuals, not out of your own notes: a fixed or allowlisted egress IP, a static hostname, an inbound webhook reachable from the public internet, a minimum TLS version, a specific cipher or certificate chain, a runtime extension, sub-minute cron, long-running or background processes, persistent local filesystem, outbound ports other than 443, a clock within N seconds of theirs, a fixed timezone. **Cite each to its page**, exactly as S18 requires.
2. **Write down what the target environment actually provides.** Not the environment you develop on — the one the thing ships to, named: this host, this plan, this tier. Shared hosting, a container platform that rotates egress, a serverless runtime with no persistent disk, a PaaS that recycles processes, a corporate network with an outbound proxy.
3. **Cross them. Every requirement against every environment the system is deployed to.** One row per pair. Three verdicts: **satisfied** (say how it is known, not assumed), **not satisfied** (a finding, graded on what stops working), **unknown** (a question for the host, and a finding until answered).
4. **Grade an unknown as a finding, not as a gap in the report.** "The host may or may not have a stable egress IP" is the state in which a launch is planned around a capability nobody confirmed.
5. **Say what breaks, in the system's own terms.** Not "IP allowlisting may be required" but "parcels cannot be booked, and the failure is a refusal from the provider that our code currently logs and does not badge"; not "WebGL2 may be unavailable" but "the editor opens to a blank canvas on the target machines and says nothing". The consequence is what gets a decision made; the requirement alone gets filed.
6. **Re-check on every environment change.** A host migration, a plan upgrade, a move from VM to container, a new region — each invalidates this sweep's result entirely, because every row was about an environment that no longer exists.

**Feed the answer back into S18.** The deployment environment is a dimension of that matrix, not a footnote to it: **a cell verified against the manual, on a host that cannot satisfy the manual's precondition, is a verified cell about nothing.**

**Grading.** A requirement the target provably cannot satisfy, on a primary path (one that moves money or goods, the user's saved work, job results or committed data): **CRITICAL**. One the target probably cannot satisfy, or can satisfy only unreliably — a shared egress IP that may rotate, a GPU feature present on the developer's card only: **HIGH**, because the failure is intermittent and intermittent failures are the ones nobody reproduces. An unknown on a primary path: **HIGH** until answered. A requirement satisfied but undocumented, so the next host move loses it: **MEDIUM**.

**And the rule this sweep leaves behind:** when an audit hands a requirement to a person as a task, it must also record *what makes the task possible* and check that. Otherwise the checklist is complete on a host where the box cannot be ticked.
**S19.1 — the capacity probe.** A host-capability table says what the host *can* do; a load
probe says what it does at the expected peak. Before launch, and before any announced peak (a
release, a batch window, a sale): drive the primary flow — the job submissions, the import, the
API's busiest route; in a shop, the catalogue, the cart and the checkout up to the vendor form —
at 1×, 2× and 3× the expected peak on **the launch host's shape** (a shared-cPanel PHP-FPM pool and a shared MySQL
saturate long before the application does) with test-mode payment tokens and sandbox endpoints only, tagged test data
(`@test-load.invalid`) for cleanup, realistic think time between steps, and the database watched
for lock waits and connection exhaustion while it runs — the application tier can look fine with
the database on its knees. The report names the request rate at which the first error appeared,
or says the probe was not run. A launch with no number here is a launch planned around a
capacity nobody measured.


Report line format: `S19 — R environment requirements extracted and cited; E environments crossed; satisfied/not-satisfied/unknown = A/B/C; table in the report.`

**S19.2 — the next-stage ladder (2026-09-17).** The Taobao notes read as fourteen stages, each
the answer to the previous stage's ceiling: one box → web and database apart → a cache → a
distributed cache → read replicas → **stateless application with a shared session store** →
load balancers and CDN → the store split by domain → services → discovery and a config centre
→ queues and polyglot stores → containers → orchestration. The lesson for an auditor is not to
recommend the ladder — a system at stage one that is pushed to stage nine is vanity engineering —
but to **audit stage N against what stage N+1 will break.** Every design that only works because
there is one process, one disk, one clock or one box is a finding *now* if the plan names a move:
sessions locked in files (the checkout's double-submit guard on this shop, §8ax), a cache that is
a PHP array, uploads on the local disk, a cron on one host, a lock that is a table row on one
connection. Write the row with the stage that breaks it, and the plan's date for that stage; a
finding with no such date is post-launch and says so.

**S19.3 — the parity matrix: the developer machine is the most permissive cell (2026-10-16).**
S19 crosses what the dependencies require against what the host provides. The same cross has to be
made against what **the suite ran on**, because a test is evidence about the environment it ran in
and nothing else — and the developer's machine is almost always the most forgiving environment the
code will ever meet. Three axes, each of which has produced a red CI under a green laptop:

1. **Engine and version.** One database engine locally while the deploy target, a CI leg or a stated
   future host runs another (MySQL locally, MariaDB on the host, or the reverse; one major version
   against another). What diverges is a list worth walking site by site: engine-specific SQL (JSON
   operators and `JSON_TABLE`, `RETURNING`, CTE and window edge cases), `information_schema` columns
   and their case and collation, DDL behaviour (implicit commits, default values on `TEXT`/`JSON`,
   online `ALTER`), what `JSON` is (a native type on one, an alias with a check constraint on the
   other), `GET_LOCK` and advisory-lock semantics, and the client programs themselves — dump and
   restore binaries whose names and accepted flags differ by engine, so a tool that shells out to one
   works only where that one is installed.
2. **Privileges.** A local account that can do everything (`CREATE DATABASE`, `PROCESS`, `RELOAD`,
   `SUPER`, routines and triggers) where shared hosting and many CI services grant one database and
   little else. A test that creates a scratch database, a tool that reads a `PROCESS`-gated table or
   sets a global variable, a dump that asks for routines — each passes locally and fails there.
3. **Secrets present or absent.** Locally the `.env` holds every secret, every time, so a code path
   that **wrongly requires** one is never exercised without it — a list-only or dry-run tool that
   resolves the database password before discovering it needs no connection, a health check that
   reads a key it never uses. CI (forks, unprivileged jobs, a fresh runner) is usually the first place
   the secret is missing, which makes it the first place the wrong dependency shows.

**Method.** Write the matrix: one row per environment the code runs in — developer machine, each CI
leg, staging, the production host, and every host or engine a stated move names (S19.4) — with
columns for engine and version, the account's privileges, secrets present or absent, OS and
filesystem (case sensitivity, bind-mount quirks), and runtime version. Then one cell per suite ×
environment: **RAN** with that run's count line pasted, or **NOT RUN**. Reproduce the cells you do not
have before pushing, not after: a throwaway container of the other engine on a spare port, a second
account granted exactly what the target grants, and one run with the secrets unset (an empty `.env`,
`env -u`). CI is where a cell gets confirmed, not where it gets discovered (S20.6).

**Grading.** A single-engine run is **not a green light** when the deploy target or a stated migration
target is another engine: that cell is UNVERIFIED, and on a path that stores the primary state it is a HIGH
finding until it is RAN. A privilege the code needs that the target account lacks is graded as S19
grades any requirement the host cannot satisfy. A code path that demands a secret it does not use:
MEDIUM — it fails the first unprivileged run and it means the tool cannot run where the secret must
not be.

**Worked example (mixoweb, 2026-10-14..16).** Every suite was green on the laptop, against MySQL, with
an account that could create databases, and with `.env` populated. CI's MariaDB leg went red on
engine-specific behaviour in the dump, restore and migration-guard tooling; the restricted CI account
could not do what the laptop's could; and a list-only restore command failed because it resolved the
database password from an environment that, for once, did not have one. None of the three could fail
on the machine the code was written on, and all three had been called green.

Report line format: `S19.3 — E environments × S suites; RAN R / NOT RUN N (matrix in the report); engines run <list> of engines named by deploy and migration targets <list>; restricted-account run: yes/no; secrets-absent run: yes/no.`

**S19.4 — migration readiness: a backup that has never been restored somewhere else is not a migration plan (2026-10-16).**
Runs whenever the owner has stated a future move — host to host, engine to engine, shared hosting to a
VPS, one region to another. "Backup and restore exist" is a claim about two tools; readiness is a claim
about a round trip **across the boundary the move crosses**, and only a drill makes it. Require:

1. **Dump on A, restore on B**, where A is the current engine and version and B the target's (a
   throwaway container of B is enough).
2. **Compare, per table**: row counts, and `CHECKSUM TABLE` — or, where a column type makes the two
   engines' checksums incomparable, an ordered-row hash, saying which tables needed it and why.
   **Compare the file stores** (uploads, private downloads, generated documents) by a hash manifest.
3. **Smoke B through the application**: log in, open a recent record, exercise one download or
   export. A restore whose data is right and whose logins all fail because a salt or app key did not
   travel is the commonest failed migration there is.
4. **Write the lay-person procedure**: numbered steps the owner can follow without the developer,
   naming each program, where every secret that must travel comes from, and how to tell it worked.

**Grading.** A stated move with no cross-engine drill: HIGH — it is the data-loss class, deferred to the
day of the move. A drill with row counts only and no checksums: its cells are PARTIAL. A drill with no
lay procedure: MEDIUM, because the person who will run it is not the person who wrote it.

Report line format: `S19.4 — move stated: <A → B | none>; drill: <date, A engine@version → B engine@version, T tables, counts equal C/T, checksums equal K/T, files hashed F> | NOT RUN; lay procedure: <path | none>.`

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
5. **Then ask the recursive question, and answer it once rather than forever.** Who watches the watcher? The regress terminates only by leaving the system: an exit code a scheduler mails, an external uptime probe, a dead-man's switch a third party trips when a ping stops arriving. **Name the outermost check and confirm it is outside the process it watches.** A monitor inside the thing it monitors shares its failures. **And confirm what it touches is the code a real request runs** — outside the process is half the test; a probe whose endpoint answers before the application boots stays green through the outage it exists to catch (2026-10-22, below).
6. **Test the blind case explicitly.** A detector's test suite must contain "it examined nothing and said so". That test is almost never written, because it feels like testing the absence of work — it is testing the difference between silence and safety.

**Grading.** A detector on a primary or safety path that cannot distinguish blind from clean: **HIGH** — every run it makes is uninterpretable, including the ones already filed as green. A scheduled job critical to the primary quantity (money, backups, sync, expiry, job results) with no liveness signal: **HIGH** — and a heartbeat that is written and read by nothing *is* no liveness signal (grade the job HIGH, not the missing reader MEDIUM). A detector whose output reaches no human surface: **HIGH** (S16 rule six). No outermost check outside the system: **MEDIUM**, and it is the one to state plainly rather than grade, because it is an architectural choice the owner should make knowingly.

**The sentence to carry out of this sweep:** *a green report from an instrument nobody has proved is looking is not evidence of health — it is evidence of a report.*

**S20.1 — advancers are watched like detectors (2026-09-14).** Step 1 says *enumerate the detectors*,
and a roll call that did exactly that reported twelve of twelve watched for liveness the day before
an audit found the one scheduled job nothing watched: the sweep that cancels unpaid orders and
returns their stock. It is not a detector — it detects nothing, it *advances* state — so it was
outside the list, marked non-critical, with no heartbeat, and outside the in-app fallback that
backed up the payment workers. A lost crontab line on a new host would have held stock for orders
nobody will pay, for ever, with no screen saying so. **Enumerate every scheduled job whose absence
changes the primary quantity or a user's promised state — money, stock, a backup, a sync, an
expiry, a queued job's result — detector or not, and demand the same three
things of each: a liveness signal something reads, a screen, and a place in the fallback if one
exists.** The question is not "what does this job find" but "what stops happening when it stops".

**Studied against three public collections (2026-09-15) — `finsilabs/awesome-ecommerce-skills`
(178 shop-ops guides), `jmr85/e2e-agent-skills` (Playwright conventions),
`DominikCLK/eCommerce-tests` (a worked Playwright shop suite).** What they had that this skill
did not: the *shape* of a rendering walk (page objects, session reuse, artefacts on failure only,
selector priority — now `references/browser-walks.md`); the capacity probe as a pre-launch step
(S19.1); business rates and CSP violation reports as detectors (S20.2); the dispute row's three
facts (S16.2); the identity a limit counts (S2.1); audit rows that carry the state before as well
as after (doctrine §8, cia). What this skill has that they do not: the sweeps themselves — a
guide says "make handlers idempotent"; a sweep says *which* handler, *which* key, and what the
operator sees when it is not. The two are not rivals; the guides say what good looks like, the
sweeps find where it is not.
**S20.2 — symptoms, not causes; business rates as detectors (2026-09-15).** The monitoring guides
say the thing the roll call can miss: a dashboard can be green while the system's real output is
down. Two detectors belong on the roll call that are not jobs at all: **the business rate** — the
primary throughput against its own history (jobs completed per hour, exports or saves per day, sync
or import success rate; in a shop, orders per day against the last weeks, payment success rate, the
mix of decline reasons — `insufficient funds` is the customer; `do not honor` in a cluster is the
issuer or fraud) — with a floor that raises a notice when the system goes quieter than it has ever
been on that weekday; and **the symptom probe** — a scheduled synthetic walk of the primary flow
from outside the host (to the vendor form, in a shop), so a 3 a.m. outage is found by a robot and
not by the morning's first user. Alert on the
symptom (success rate below a floor for longer than a blip), link the runbook, and start with
three alerts, not thirty. And one signal that is a detector in disguise: **a Content-Security-
Policy violation report from a payment page** is a Magecart alarm — route it to a person, not
a log.

**S20.3 — the receipt is written by the worker, never by its parent (2026-09-16).** A seven-hour
test run was launched through a wrapper that, when the run returned, appended `EXIT=<code>` to the
log — the line the handoff said to look for. The session that launched it was cleared; the
wrapper died and the worker did not. The run finished green, the tool's own summary line was in
the log, and `EXIT=` never came. The watcher polling for it reported *process gone, no exit line*
on a passing run. **Any end-of-run marker written by a launcher, supervisor, cron wrapper, shell
`&&`, CI step or parent shell is a watchdog that can die before the thing it watches. Read the
marker the worker writes itself** — the test runner's summary, a JUnit or JSON result file, a
row the job commits on its last line — **and treat the parent's marker as a bonus.** Apply the
same test to every scheduled job in the roll call: if its "finished OK" line comes from cron's
mail, from a wrapper script or from the process that forked it, the liveness signal something
reads (column H) is not the job's own, and a dead wrapper reads as a job that never ran. The
unambiguous shape is one signature: *worker gone, no worker-written marker* — that, and only
that, means the worker died.
**And know what the worker's marker looks like at each moment.** PHPUnit's `--log-junit` file
is created *empty* when the run starts and written when it ends; a watcher that treated the
file's existence as the end fired thirty seconds into a seven-hour run. The start of a marker
and the end of a marker are different facts — an empty file, a closing tag — and the watcher
names which one it is waiting for.


**S20.4 — liveness is not readiness (2026-09-17).** Orchestrators separate two probes for a
reason, and any system's safety net should too: **liveness** — the process is running and its
heartbeat is fresh — and **readiness** — it may take work, because what it depends on is
reachable. A worker that is alive and whose gateway is unreachable is *live and not ready*: the
right response is to stop taking that work and say so, not to restart it and not to count it
green. The maintenance door is the application's own readiness switch — closed on purpose — and a
health page that says "up" while the door is closed, or "up" while the database is gone, is a
liveness answer to a readiness question. For every detector and worker on the roll call, ask which
of the two its signal is, and whether anything asks the other.

**S20.5 — a walk receipt proves the moment it was taken, not the day after (2026-09-20).** A headless walk logged into the admin, read the rendered menu and recorded five tabs with the right rows and order — proof, with a timestamp, that a menu-grouping hook was live. The next morning an environment fault killed it: a Docker bind mount whose `rewinddir()` returned a single entry made the installer see one of forty-eight modules, so a routine install run inside the container poisoned the module cache and every autoloaded module — the nav hook included — went silently off, with the admin back to a flat, ungrouped list and no error anywhere. The walk's receipt was still sitting in the report, true when written and false by the time anyone read it again. **A receipt is evidence for the run that produced it, never a standing guarantee** — treat "proven live" as dated, not closed, and demand the detector live *in the product*: a badge or panel an operator sees every day they open the screen, not only a line in an audit's output that nobody re-runs until the next audit.

**S20.6 — the CI run nobody read (2026-10-16).** CI is a detector, and a detector whose verdict
lands in an inbox nobody opens is the dead watchdog in its most ordinary form. **A push is not done
until the CI run for that commit has been read**: its id, its conclusion, and for a red, the first
failing job and step. In the worked example two pushes went out with a red CI that nobody looked at,
and the owner learned it from the hosting platform's failure e-mail — the outermost check fired, and
reached the one person who could not act on it.

**Audit check.** For the commit audited, report the latest CI run id and conclusion (for GitHub:
`gh run list --commit <sha> --limit 1 --json databaseId,status,conclusion`). `not checked` is itself a
finding — MEDIUM, HIGH on a green-light request — and so is a CI that is configured and has not run on
the audited commit, and so is a red on any earlier commit of the branch that nothing has explained.
The verdict has to reach a person, not only a mailbox.

**And the budget rule.** CI minutes can be the scarcest resource a small project has (a free plan, no
budget for more), and every push spends them. Reproduce the CI cell locally first — S19.3's other-engine
container, restricted account and secrets-absent run — push rarely and in batches, and never re-run a red
without a written hypothesis of why it would now pass. A speculative re-run spends the budget on a
question a local reproduction answers for nothing; and a red that turns green on re-run is a flaky test,
which is an S21 finding, not a pass.

Report line format: `S20 — D detectors enumerated; C report coverage separately from findings; H have a liveness signal something reads; E escalate to a human surface; outermost check: <named, or NONE>.`

## S21 — The suite is an instrument too. A PASSING ASSERTION THAT SOMETHING IS EMPTY PROVES NOTHING UNTIL SOMETHING PROVES IT CAN BE NON-EMPTY

S20 asks whether the detectors are looking. **S21 asks it of the test suite**, which is the detector everything else is trusted on. Fourteen shapes. The first six are a test that never ran or never asserted; the last eight ran and asserted, on something other than the claim in their name — seven claiming more than they had, and one claiming less. The first four were confirmed in one codebase in one day, the sixth days later in the same one, and shapes 7 to 14 on 2026-09-24 in a single day across two sessions auditing one tree:

1. **The vacuous pass.** A query used by four tests returned nothing at all, because of a defect none of them was about. The two tests asserting *"and the result is empty"* passed — that is what they asked for — and the two asserting a result failed. The failures looked like a test problem precisely because their siblings were green. **Whenever the subject of a test is a query, a filter, a collection or a sweep, at least one test must prove it can return something, under the same conditions.** And watch the **assertion count**, not only the colour: if fixing a bug makes assertions go *up*, assertions were not being reached, and every earlier green run was reporting on code it never executed.
2. **The runner is one environment.** A test that loads real configuration into the runner's own process — a framework bootstrap, a config builder, a dotenv loader, anything that reaches the production entry point — changes `getenv()` for every test that runs after it, across suite boundaries when the suites share a process. The damage reads as an order-dependent flake and hides for months. **Snapshot the environment before such a test and restore it after.** And the asymmetry that makes this so hard to see: **cleaning up in teardown protects the next test and never the first.** A test that depends on the *absence* of a variable must clear it on the way **in**.
3. **The failure diff is an output channel.** A test that asserts on a credential, token or key prints the real value in full when it fails — into scrollback, into CI logs, into whatever a reviewer pastes. Codebases that carefully refuse to quote a secret in an error message routinely quote one in an assertion. **Assert on a derived property** — length, prefix, "not the plaintext", "not equal to what is stored" — **or clear the source so the comparison cannot reach a live value.**

4. **A guard that exists but runs too late is a latency gap, not a coverage gap — and the two have different fixes.** A missing test is written; a slow one is *moved*. An admin page had been throwing on every render for days. A test asserted exactly the invariant that broke and would have named it precisely — but it was test 4555 of 4875, four hours into a seven-hour suite, so in practice nobody had reached it since the defect landed, and the first witness was seven errors in an unrelated class four hundred tests earlier, which is why it read as a test problem rather than as a dead page. **For every invariant a slow suite protects, ask what it actually costs to check.** Reflection over two constants, a schema-versus-code comparison, a "every X has a Y" pairing — these need no database and no fixtures, and belong in whatever tier runs before a commit. The one that was moved went from unreachable-in-practice to **0.135 seconds**. When a suite is slow enough that people stop running it, its guards have already stopped guarding, whatever the coverage report says.

5. **The self-consistent codec.** A round-trip test — encode then decode, sign then verify, serialise then parse — proves only that the code agrees with itself. Against any external protocol, file format or partner API that is not the question; the question is whether it agrees with the *other side*. A payment-gateway codec passed a round-trip selftest for a day before anyone checked it against the vendor manual's own worked example (which printed key, IV, plaintext and the expected ciphertext and digest); a signature test reproduced the vendor's published example but its "sort order matters" sibling was vacuous — every key in the example started uppercase, so the two sort rules gave the same answer and the test could not fail. **For every external protocol the code speaks, find the counterpart's published example and a test that reproduces it byte-for-byte; then find the negative that can actually tell** (inputs the two rules order differently, a wrong key, a tampered digit) **and prove the test goes red when the vector is tampered.** A codec without a counterpart vector is a hypothesis with a green badge.

6. **The runner's own file listing is an instrument (2026-09-20).** A suite discovers its tests by walking directories; walk it in an environment whose directory iteration is broken and it discovers fewer of them and prints the same green `OK` over the smaller number. One laptop's Docker bind mount returned a single entry from `rewinddir()`, so the fast suite run inside the container found 2,370 tests where the host found 3,137 — 767 tests silently not run, no warning, exit 0. The count is the measurement: every run quotes its discovered-test total against the last known one (`--list-tests | wc -l` on the same commit), and a green run over fewer tests than yesterday is a red run until the difference is explained. The same iteration fault had already poisoned the product's module cache in the same environment (S20.5) — one broken primitive, two storeys of silence.

**Shapes 7 to 14 share a sentence worth saying before them: _the thing that made it pass was not
the thing it claimed to prove._** Every one of them is green, runs, and asserts. Coverage counts
the lines. The assertion count goes up, not down. What fails is the correspondence between the
claim on the tin and the thing the assertion actually constrains — which is why none of the first
six catch them, and why they are found by reading a test against its own name rather than by
running anything.

7. **The test that pins the defect.** A product page published `variants[0]`'s stock as the whole
   product's availability, so an item with one sold-out variant and one in stock went to Facebook
   and Google as `out of stock` while the shop accepted orders for it. The renderer's test file
   had an assertion for it — it asserted the template read the *variant's* purchasability. **The
   defect had a passing test holding it in place**, and the fix turned the suite red, which reads
   to whoever runs it next as the fix being the regression. **When a finding is confirmed, grep
   the suite for an assertion that encodes the defective behaviour before writing the fix.** If
   one exists: the finding is *stronger*, because somebody wrote the wrong behaviour down
   deliberately and it is therefore load-bearing somewhere; the fix must **replace** that
   assertion rather than add beside it, with a comment saying the old one pinned a defect; and ask
   what else that author pinned. This is the inverse of a missing test and invisible to coverage —
   the line is covered, by an assertion that it stay wrong.

8. **The injection that never arrived.** Proving a fallback needs a fault, and the obvious
   injection is the blunt one: take the table away, kill the connection, delete the file. The
   blunt injection frequently **never reaches the code under test**, because an earlier guard
   refuses first and the test goes green on the refusal. Concretely: a checkout falls back to a
   standard tax rate when settings cannot be read; the test hid the settings table; checkout
   refused at `shipping-method-unavailable`, and for a basket that skipped shipping at
   `payment-window-unavailable` — both read settings *before* the tax read. Every assertion about
   the fallback was unreachable. It was caught only because one refusal message differed from the
   expected one; reword that message and the test is green for ever over a path it never entered.
   **An injection test must assert that the injection arrived, not only that the system behaved.**
   Three things make it hold: prove the fault reached the frame under test (a counter the injector
   increments, its distinctive exception asserted in the log, or an observable only the fallback
   produces); **key the injector on the call frame, never on a query count, an ordinal or a
   timing**, so an unrelated call added later cannot move the injection or silence it — and name
   the frame by symbol, so renaming the method turns the suite red instead of turning the injector
   into a no-op; and **assert the guards that fire before it**, because they are the reason the
   interesting case is the one it is. The reachability question comes first and changes the
   finding itself: **before filing "silent fallback", ask what refuses before it.** A fallback
   behind guards that refuse under the same conditions is reachable only in a narrower window —
   usually a failure *during* an operation rather than a sustained one — and that window is what
   the proof has to reproduce.

9. **The proof that re-implements the cases it tests.** A walk suite's resilience to re-theming
   was to be proved by renaming CSS classes and re-running the walks. The proof re-implemented
   four abbreviated inline copies of walks instead of running the real ones, and the two it
   omitted were exactly the two depending on the selectors the injection renamed. It reported
   *"3 of 4 passed unmodified"*. None ran unmodified, and the ones that would have failed were not
   among the four. **A proof that re-implements its subject proves the re-implementation.** Two
   rules: a resilience, migration or compatibility proof must invoke the real artefact through the
   same entry point production uses, and if it cannot, *that* is the finding; and **when a proof
   tests a subset, the selection rule must be stated and must be independent of the outcome** —
   "all of them", "the four fastest", "four at random, seed recorded" are rules, while "four of
   them" is a result dressed as a method. The tell is a denominator that does not match the
   population: *3 of 4* where the population is 6.

10. **Claim-versus-assertion drift.** A browser walk's own docstring said it verified the cart and
    checkout routes and that the CSP `form-action` listed the configured gateway hosts. It
    asserted **four of the nine hosts the code configures**, on the cart route only, and the
    missing four included the production host the check existed for in the first place. It also
    read different headers than it named. Everything it asserted was true; the sentence describing
    it was not — and the sentence is what gets quoted into a report. **Read every test's name and
    docstring as a claim, then check the assertions against it.** Where the code enumerates a set —
    hosts, providers, statuses, locales, roles, permissions — a test that names the set and asserts
    a subset is *worse* than one asserting nothing, because it is counted as coverage. **Assert
    against the enumeration itself rather than a copied list**, so adding a member fails the test
    until somebody decides about it. And quote ratios in report lines: *asserted 4 of 9 configured
    hosts*, never *"hosts verified"*.

11. **The textual guard that passes on a variant of what it forbids.** An architecture test
    forbade a MySQL-only JSON operator by matching raw token text. A developer escaping the dollar
    out of habit — `"col->>'\$.a'"`, an escape PHP does not need — moved the operator out of
    matching position and **the guard passed, silently, by accident, on exactly the dependency it
    existed to stop.** **Every guard that matches source text has variants, and a green textual
    guard is evidence of nothing until its limits are written down.** The fix is not a better
    regex. Enumerate the evasions — concatenation across lines, heredoc and nowdoc bodies, a
    `sprintf` template, a variable interpolated back, whitespace inside the construct, an
    unnecessary escape — and pin each in a data-provider test as **caught-with-proof** or
    **knowingly-not-caught-with-reason**; prove that a stale exemption turns the guard **red**
    rather than permissive, and that an exemption opens one line rather than the file. Then say the
    conclusion out loud, because it is the part that gets left off: **the shapes a per-token
    matcher cannot see are closable only by behaviour** — running the thing against the other
    engine, the other runtime, the other version. A textual guard's real output is a list of what
    still needs a behavioural check. **And a guard that names a remedy must have one that
    resolves** — for every guard whose failure message points at a replacement ("use `Lines::raw()`
    instead"), check the replacement exists and does what the message claims. A guard teaching a
    fix nobody can apply is the orphan-capability problem (S13) in a place nobody looks for it, and
    it is cheap to check: the message names a symbol, so resolve the symbol.

12. **The assertion that cannot fail.** A walk checked that an empty state was actionable by
    raising only if a page-wide "Shop" link **and** every `main a` were absent. The header nav
    guarantees the first on every page, so the conjunction could never be true and the check could
    never fail — it ran, asserted, and was structurally incapable of finding anything. Its sibling
    read console errors from `getattr(page, "_walk_console_errors", [])`, which returns the empty
    default on any page not built by the expected factory and passes; the resilience proof built
    pages exactly that way. **Every default on an assertion path is a candidate vacuous pass.**
    `getattr(x, name, default)`, `?? []`, `dict.get(k, [])`, an `or []`, a nullable that silently
    coalesces — each turns "I could not find the evidence" into "there was nothing to find", which
    are opposite reports. Two checks: **write the negative first** and watch the assertion go red
    before it goes green, which an unfalsifiable conjunction cannot do; and for every default in a
    check, ask what reaches it *other* than the intended empty case, then assert the value was
    actually populated rather than merely empty.

13. **Structure counted as coverage.** A shared base class carrying a route checklist existed, was
    genuinely shared, was well written — and was invoked on **one route of fourteen**. The coverage
    claim was made from the existence of the mechanism rather than from its use, and every sentence
    in that claim was true about the class. **Count call sites, not definitions.** A helper, a base
    class, a decorator, a mixin, a fixture, a lint rule: the number that matters is how many of the
    population actually go through it, over the population the code itself enumerates. A mechanism
    adopted by a tenth of its subjects is a proposal, not a control — and it reads, in every
    report, exactly like one adopted by all of them.

14. **The vacuous failure — a check that reports red for a non-reason.** Every shape above is a
    proof claiming more than it has. This is the mirror, and it belongs here rather than as a
    footnote because its harm is slower and more durable. A deploy-rehearsal probe returned `FAIL`
    on a healthy machine; the only failing row was a required-extensions list naming three PHP
    extensions. Grepped for actual usage with symbol patterns rather than by plausibility: two were
    referenced **nowhere** in the source, and the third was real but sat behind an explicit
    `function_exists()` fallback that degrades rather than breaks. The list had been assembled by
    plausibility, which is the default state of every requirements list. **A vacuous pass costs a
    false green once. A vacuous failure trains the operator to ignore the instrument** — the second
    red is scrolled past, and so is the tenth, and so is the one that meant something. It is alert
    fatigue arriving by a correctness route rather than a volume route: one check, wrong once,
    permanently discounted. It is worst where the reader cannot triage what they are shown, because
    a verdict somebody is not equipped to evaluate burns the one signal they had — and it inverts
    *nothing dies quietly*, since the thing dying quietly is the operator's attention, which
    reporting louder makes worse rather than better.
    **The check: for every condition that can fail a verdict, is the condition actually required,
    and is that established by evidence or by assumption?** Sort them — hard requirement (proved by
    a reference to it), soft with a proven fallback, and unreferenced — and let exactly one of the
    three turn a verdict red. Two riders. **The instrument finding outranks the finding that
    exposed it:** "is this extension on the host" is a LOW-MEDIUM capability question, while "the
    probe fails for non-reasons" is a defect in the thing that answers all such questions, so when
    a check misfires, grade the check and not only its subject. And **a soft dependency reports its
    consequence, not its absence**: *"gd missing"* tells an operator nothing, *"gd missing — product
    images serve at full size instead of resized"* tells them whether they care. An absence is not
    a finding; a consequence is.

Method: enumerate the tests that touch the system's real configuration or entry points; confirm each restores what it changed. **Read a sample of test names and docstrings against their assertions** — where a claim names an enumerated set, count what it actually asserts and quote the ratio. For every test that injects a fault, find what proves the fault arrived; for every guard that matches source text, find where its known limits are written down. For every suite that asserts emptiness, find the sibling that proves non-emptiness. Record the assertion count alongside the test count in every claim, because *"N tests pass"* and *"N tests ran and asserted M things"* are different reports. For every external protocol, name the vendor-published vector the suite reproduces, or write "none — round-trip only".

**Grading.** A vacuous pass on the primary path or on a safety net (the monitor, the reconcile, the watchdog — anything whose job is to notice): **HIGH** — the code it was meant to cover has never been exercised, and a safety net that has never been shown to fire is a detector nobody has proved is looking (S20). "Money path" is the commerce special case; in a job runner the primary path is the job. Environment contamination that reaches other tests: **HIGH** when the contaminating values are real credentials, **MEDIUM** otherwise. A live secret reachable in failure output: **HIGH**, and say it in the conversation with the rotation decision attached, per §0.11. **An assertion that pins a defect** (shape 7): the severity is the defect's, and the pinned assertion is reported beside it, because it is the reason the defect survived review. **An injection test whose fault cannot be shown to have arrived** (shape 8), or a **proof that re-implemented its subject** (shape 9): grade as the coverage the artefact claimed and does not have — so a resilience proof over a primary path is **HIGH**, and the report says the claim is withdrawn, not merely qualified. **Claim-versus-assertion drift** (shape 10): **MEDIUM**, and **HIGH** when the un-asserted members include the one the check exists for. **A textual guard with no written limits** (shape 11): **MEDIUM** on its own and **HIGH** where the thing it guards is a portability, security or compatibility boundary that nothing else checks.

**The sentence to carry out of this sweep:** *green is a colour, not a measurement — quote the counts, and know which of them went up.* And beside it, the question that organises shapes 7 to 14 and is a better one than *is this tested?*: **what, exactly, made this pass or fail — and is that the same thing it claims to prove?** Both ends of that question matter: shape 14 is the same root asked from the failing side. Every one of those seven is an instance of the answer being no, and each wore a different costume: a pinned assertion, an injection that never landed, a re-implemented proof, a docstring wider than its asserts, a guard matching text, a conjunction that cannot be false, a mechanism counted by its definition. None of them is found by running anything. All of them are found by reading an artefact against its own claim.

Report line format: `S21 — T tests / A assertions quoted; V vacuous-pass risks found; E tests that mutate the runner environment, R of them restoring it; S secrets reachable in failure output; K of P external protocols pinned to a counterpart-published vector; D assertions that pin a defect; I of J fault-injection tests proving the fault arrived; C claims checked against their assertions, X drifting; G of H textual guards with written limits; U unfalsifiable assertions and defaults on check paths; M shared mechanisms quoted as call sites over population; F conditions able to fail a verdict, E of them evidenced as required rather than assumed.`

