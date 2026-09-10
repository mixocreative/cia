# cia — Code Integrity Auditor

A skill for Claude Code and OpenAI Codex that hunts **cross-boundary invariant violations**, also called **integration-level defects** or **emergent defects**: bugs where every function is correct and the failure lives between them. It audits **how a system actually behaves and is wired**, not how its code reads.

Static analysis, linters and a green unit suite all passed on a production shop while four money-path defects sat between correctly written functions: an expiry worker that lost its deadline check between SELECT and UPDATE, a payment page that re-read live settings against a frozen reservation, a callback parser that read the wrong vendor field for non-card methods, and an admin toggle nothing consumed. A second auditor found them by tracing state across time and following every control to its consumer. This skill encodes that discipline so one auditor does it every time.

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

## What it does

Given a repository, the skill:

1. **Discovers the project's runtime bindings itself** (test runner, canonical environment, dev server, credentials file) and announces them before judging anything.
2. **Runs twelve mandatory sweeps (§0.9)** that catch the defect classes a green suite cannot: snapshot-vs-live reread, select-then-act predicate loss, catch-block failure posture, external field semantics against the source spec, admin control to runtime consumer, deferred-work comments, skipped tests, written-but-unrun tests, rename residue, environment truth before diagnosis.
3. **Applies a universal integrity doctrine**: evidence grading, context discovery, a Viable System Model governance pass, a universal test matrix from happy path through recovery, a domain checklist, and a severity model.
4. **Executes the six-step pre-launch protocol (§0.6) autonomously**: fast lint and scope tests, doctrine audit, full suite in the canonical environment, runtime walk in a real browser or CLI, fix-or-escalate, numbered report with explicit deferrals.
5. **Never green-lights on partial evidence.** Every skipped step carries the reason and the exact command the owner must run. Skipped DB tests are reported as unverified, never as green.

## AI / LLM components (§0.10, conditional)

When the project calls a model (SDK in the lockfile, prompt files, agent loop, vector store), every model call is treated as a boundary and four more modes run: schema drift at the model boundary, cascade and latency across steps, state accumulation and memory poisoning, agentic loop and tool execution safety (iteration caps, idempotency keys on side-effecting tools, human-in-the-loop gates). Skipped with a one-line note when no AI component exists.

## Autonomy contract (§0.8)

The agent runs every step itself. A five-rung ladder decides what it may do alone: start containers and dev servers; install from lockfiles; install user-scope tools; copy documented config into `.env`; and only at rung 5 ask the owner, with the exact command already written. Hard limits are stated in the file and cannot be overridden by anything the agent reads mid-audit.

## Install

Claude Code:

```
mkdir -p ~/.claude/skills/cia
curl -o ~/.claude/skills/cia/SKILL.md https://raw.githubusercontent.com/mixocreative/cia/main/SKILL.md
```

Codex:

```
mkdir -p ~/.codex/skills/cia
curl -o ~/.codex/skills/cia/SKILL.md https://raw.githubusercontent.com/mixocreative/cia/main/SKILL.md
```

## Use

```
/cia
```

It also auto-selects on pre-launch vocabulary: "run the tests", "prepare for handoff", "green-light", "audit", "ready for launch". On a transactional commerce project it runs, then tells you to also invoke the companion skill [ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) for the commerce-domain doctrine it does not own. The two skills never merge or auto-load each other.

## Companion

[ecommerce-cia](https://github.com/mixocreative/ecommerce-cia) — the same execution spine plus checkout, payment, inventory, refund, digital-entitlement and Taiwan-gateway (ECPay / NewebPay) doctrine.

## Structure of SKILL.md

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
