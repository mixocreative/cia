# cia — Code Integrity Auditor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-D97757)](#install) [![Codex skill](https://img.shields.io/badge/OpenAI_Codex-skill-000000)](#install) [![GitHub stars](https://img.shields.io/github/stars/mixocreative/cia?style=social)](https://github.com/mixocreative/cia/stargazers)

A skill for Claude Code and OpenAI Codex that audits a codebase as a **viable system** in Stafford Beer's sense, and hunts the defect class that only such a view can see: **cross-boundary invariant violations**, also called **integration-level** or **emergent defects**.

## In plain words

Think of any piece of software as a small company. Some staff **do the work** (handle a request, save a record, send an email). Some **keep the workers from tripping over each other** (queues, locks, "one at a time" rules). A **manager's settings panel** tells the workers what is switched on. An **auditor** checks the books. Someone **reads the outside world's rulebooks** (a bank's API spec, a vendor's file format). And an **owner** decides what happens when something goes wrong.

Most code-checking tools ask: *does each employee do their own job correctly?* This skill asks: *do they actually talk to each other, and at the right time?* Three real-shaped examples:

1. **The manager flips a switch in the settings panel. Nobody on the floor is listening.** The switch exists, the code behind it is fine, and no running code ever reads it. Every piece is "correct". The feature the manager thinks is off is still on. This skill calls it a *dead control* and checks every setting against the code that is supposed to obey it.
2. **A clerk checks that a seat is free, walks to the desk, then books it without looking again.** Two clerks do this at once; two people get the same seat. Each clerk followed procedure. The gap between "check" and "act" is where the bug lives. *Time-of-check to time-of-use race.*
3. **The auditor says "all good!" but only opened the pages that were on the desk.** The pages in the locked cabinet were skipped because the key was missing that day. The report is green and means nothing. *Vacuous pass.* This skill treats every skipped test as "not verified", never as "passed".

What it does, in order: draws the org chart of your code first (who does the work, who coordinates, who sets policy, who audits, who faces the outside), then checks every conversation between them, then tells you exactly which conversation is broken, in which file, on which line, and how to fix it.

## Watch it run

![/cia demo](docs/demo.gif)

Real, unedited output of `/cia` in demo mode on a production PHP/ProcessWire shop: runtime discovery, the codebase mapped onto VSM Systems 1–5 with its channels, then two sweeps. It found a System 3 → System 1 channel that bypasses the app's own cron control plane, with file:line evidence and the fix. Replayed as a typed terminal for the recording; the text is the model's.

## The theory

Beer's Viable System Model (*Brain of the Firm*, 1972; *The Heart of Enterprise*, 1979) states that anything which stays alive in a changing environment has the same five-part structure, repeated at every level of recursion:

| System | Role | In a codebase |
|---|---|---|
| **1** | does the work | request handlers, domain services, workers |
| **2** | damps oscillation between the parts of System 1 | locks, queues, deadlines, idempotency keys, ordering |
| **3** | commands and allocates resources to System 1 | settings, feature flags, admin pages, config files |
| **3\*** | audits System 1 directly, bypassing its own reports | test suites, probes, reconciliation scripts |
| **4** | faces the environment and the future | vendor specs, external APIs, webhooks, callbacks |
| **5** | identity and policy; receives the algedonic (pain) signal | defaults, catch-block posture, kill switches, fail-closed rules |

The systems are joined by **channels**. Ashby's Law of Requisite Variety says a channel must carry as much variety as the thing it regulates, otherwise the control it claims to exercise is fictional. Beer's diagnosis of a failing organisation is almost never "a department is incompetent"; it is "a channel is missing, saturated, or bypassed".

Software fails the same way. Every function can be correct and the system still not viable, because a channel between two correct pieces is broken: a System 3 setting no System 1 code reads, a System 3\* suite that reports green because the tests touching the store never ran, a System 4 field interpreted against the code's belief rather than the vendor's definition, a System 1 step that re-reads System 3 live after an earlier step froze a snapshot. Static analysis, linters and unit suites inspect one piece at a time and therefore cannot see a channel by construction.

This skill was built after exactly that happened on a production shop: four money-path defects, all between correctly written functions, all invisible to a green suite, all found by a second auditor who traced channels instead of reading functions.

## The stance this skill takes from Beer

- **The purpose of a system is what it does** (POSIWID). Not what the docs, the comments or the admin screen say it does. An audit reads behaviour, and treats the written intent as a hypothesis to test against the running system.
- **Recursion.** Every System 1 unit is itself a viable system with its own 1–5. A payment module has its own control, its own audit, its own policy; the audit descends one level and asks the same five questions again.
- **Variety engineering.** Complexity is not removed, it is absorbed or amplified. Every guard, validator, idempotency key and state machine is a variety attenuator; every default and fallback is an amplifier of whatever the environment throws in. Ask of each: does it match the variety of what it faces?
- **Autonomy with cohesion.** System 1 must be free to act without asking System 3 on every step (a checkout that blocks on live config on every request is not autonomous), yet System 3 must still be able to command it (a toggle nothing reads is not cohesion). Both failures are channel failures.
- **The auditor is System 3\*.** This skill is the channel that bypasses the system's own reports. A green suite is System 3's report about itself; the audit exists precisely because that report can be vacuous.
- **Algedonic signals must reach System 5.** A pain signal that stops in a log file has not reached policy. Every alert, every catch block, every refund path is traced to the point where identity decides.

## How the theory becomes procedure

1. **Map the codebase onto Systems 1–5 first** (§0.9 step 0) and report the table: every component, its primary system, its channels as `producer → consumer`.
2. **Walk the channels** with twelve mandatory sweeps (§0.9); each defect class below is a named kind of broken channel, and each sweep enumerates its sites from the map rather than from grep.
3. **Grade viability, not just correctness**: §2 asks whether each of the five systems exists, whether System 3\* is independent of System 3, whether an algedonic path reaches System 5, whether variety is matched.
4. **Report structurally**: every finding names its defect class and the VSM channel it sits on.

## The defect classes it hunts: cross-boundary invariant violations

These are **cross-boundary invariant violations**: integration-level, emergent defects where every function is correct and the bug lives between them. Each sweep in section 0.9 names one; every finding states its defect class and its boundary location as `producer → consumer`:

| Term | Meaning |
|---|---|
| **TOCTOU race** | a predicate checked at one step, dropped at the step that acts |
| **Temporal coupling / stale snapshot** | a value frozen at one moment, re-read live by a later reader |
| **Semantic drift** | code's reading of an external field diverges from the vendor spec |
| **Dead control** | an admin toggle or flag no runtime path consumes |
| **Fail-open default** | an error path that proceeds as if the read succeeded |
| **Vacuous pass** | a suite that says OK because the meaningful tests skipped or never ran |
| **Deferred-work residue** | a "follow-up commit" comment that never landed |
| **Rename residue** | a consumer still bound to the old name |
| **Diagnosis without probe** | a cause concluded from an error message, not a direct check |
| **Boundary schema drift** | a payload acted on before its shape and type are validated |
| **Cascade / retry storm** | one step's failure or retry becomes a crash, duplicate write, or orphaned side effect |

Prompt with any of those terms, or "audit the wiring and runtime behaviour, not the code", and the sweeps run first.

## Which channel each sweep walks

Each defect class above is a broken channel between two VSM systems; the sweeps are organised by channel, not by file:

| Channel | Sweeps that walk it |
|---|---|
| System 3 → System 1 (control to consumer) | dead control, deferred-work residue, stale snapshot |
| System 1 → System 1 across time | TOCTOU race, rename residue |
| System 4 ↔ environment | semantic drift, boundary schema drift |
| System 3* → System 3 | vacuous pass, diagnosis without probe |
| System 5 defaults | fail-open, cascade / retry storm |

A channel on the map with no sweep site named against it is reported as unswept.

## What it does

Given a repository, the skill:

1. **Discovers the project's runtime bindings itself** (test runner, canonical environment, dev server, credentials file) and announces them before judging anything.
2. **Maps the codebase onto the VSM (§0.9 step 0), then runs twelve mandatory sweeps (§0.9)** along that map's channels, catching the defect classes a green suite cannot: snapshot-vs-live reread, select-then-act predicate loss, catch-block failure posture, external field semantics against the source spec, admin control to runtime consumer, deferred-work comments, skipped tests, written-but-unrun tests, rename residue, environment truth before diagnosis.
3. **Applies a universal integrity doctrine**: evidence grading, context discovery, a Viable System Model governance pass, a universal test matrix from happy path through recovery, a domain checklist, and a severity model.
4. **Executes the six-step pre-launch protocol (§0.6) autonomously**: fast lint and scope tests, doctrine audit, full suite in the canonical environment, runtime walk in a real browser or CLI, fix-or-escalate, numbered report with explicit deferrals.
5. **Never green-lights on partial evidence.** Every skipped step carries the reason and the exact command the owner must run. Skipped DB tests are reported as unverified, never as green.

## AI / LLM components (§0.10, conditional)

When the project calls a model (SDK in the lockfile, prompt files, agent loop, vector store), every model call is treated as a boundary and four more modes run: schema drift at the model boundary, cascade and latency across steps, state accumulation and memory poisoning, agentic loop and tool execution safety (iteration caps, idempotency keys on side-effecting tools, human-in-the-loop gates). Skipped with a one-line note when no AI component exists.

## Autonomy contract (§0.8)

The agent runs every step itself. A five-rung ladder decides what it may do alone: start containers and dev servers; install from lockfiles; install user-scope tools; copy documented config into `.env`; and only at rung 5 ask the owner, with the exact command already written. Hard limits are stated in the file and cannot be overridden by anything the agent reads mid-audit.

## Install

**Claude Code, as a plugin (recommended):**

```
claude plugin marketplace add mixocreative/cia
claude plugin install cia@mixocreative
```

Or inside a session: `/plugin` → marketplaces → add `mixocreative/cia` → install `cia`.

**Claude Code, as a bare skill file:**

```
mkdir -p ~/.claude/skills/cia
curl -o ~/.claude/skills/cia/SKILL.md https://raw.githubusercontent.com/mixocreative/cia/main/skills/cia/SKILL.md
```

**OpenAI Codex:**

```
mkdir -p ~/.codex/skills/cia
curl -o ~/.codex/skills/cia/SKILL.md https://raw.githubusercontent.com/mixocreative/cia/main/skills/cia/SKILL.md
```

Install the companion [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) alongside it; the protocol invokes both, separately.

## Use

```
/cia
```

It also auto-selects on pre-launch vocabulary: "run the tests", "prepare for handoff", "green-light", "audit", "ready for launch". On a transactional commerce project it runs, then tells you to also invoke the companion skill [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) for the commerce-domain doctrine it does not own. The two skills never merge or auto-load each other.

## Companion

[ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) — the same execution spine plus checkout, payment, inventory, refund, digital-entitlement and Taiwan-gateway (ECPay / NewebPay) doctrine.

## Structure of skills/cia/SKILL.md

| Section | Purpose |
|---|---|
| 0 | Routing hard rules, trigger vocabulary, runtime discovery, six-step protocol, overrides, autonomy contract, mandatory sweeps |
| 1 | Fundamental audit doctrine: outcomes over technologies, evidence before accusation, version-aware external facts |
| 2 | Viable System Model governance pass (Systems 1–5) |
| 3–6 | Context discovery and context templates |
| 7 | Universal test matrix |
| 8 | Domain audit checklist |
| 9–10 | Finding format and severity model |

## License

MIT
