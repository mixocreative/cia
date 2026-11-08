# Build orchestration — building a complicated application with no loose ends

> Job of this file: when the request is **build it** for a multi-part application (several surfaces, several roles, real state), say what "finished" means before the first line is written, and make every artefact carry an owner and a closing condition, so that nothing is left half-wired when the work stops. Build mode for a single primary-path write is `build-standard.md`; this file is the layer above it.
>
> Adapted from `ddunnock/specification-refiner` (SEAMS 13-category ambiguity taxonomy, Impact × Uncertainty scoring) and `ddunnock/documentation-architect` GUARDRAILS (cascade analysis, idempotent operations, memory updates in the same step); the ID scheme and the AI-assistance rules are adapted from `meddev-traceability` and `meddev-ai-assisted-development-governance` (both MIT). The closure gate is this skill's own.

---

## 1. The invariant: every artefact has an owner and a closing condition

A **loose end** is any artefact that lacks its next link. The artefacts and their links:

| Artefact | Owner link | Closing condition |
|---|---|---|
| Obligation (a promise the code must keep) | the one owner module (`evidence.md` §E3) | a proof that fails when the promise is broken |
| Capability (`C-id`) | at least one surface, or a declared system-only owner (`surface-map.md` SC1) | a `●` cell, or a named scheduled job / consumer |
| Surface (`S-id`) | the capability it invokes | handler read, state branches rendered (SC2, SC4) |
| Journey (`JRN-id`) | its exits all have an owner decision | every grid cell has a verdict (`journey-map.md` §7) |
| Doc line that describes behaviour | the code path it describes | updated in the same commit (§5) |
| Generated artefact (graph, README map, seed) | its generator command | regenerated and read back (§6) |

Nothing closes by being written. A thing closes when the link is checked.

---

## 2. The spec gate — before the first increment

Write the spec as a list of obligations, capabilities, surfaces and journeys. Then run one pass over it with the **13-category SEAMS taxonomy**, scoring each finding by **Impact × Uncertainty** (each 1–5; the product ranks the questions, 25 first):

| Group | Category | Ambiguity marker to search for |
|---|---|---|
| Functional | SCOPE | "etc.", "might include", "[TBD]" |
| | BEHAVIOR | "should", "as needed", "probably" |
| | SEQUENCE | "before/after" with no ordering rule |
| | AUTHORITY | "someone", "the appropriate person", roles not defined |
| Data & integration | DATA | a field with no type, range or format |
| | INTERFACE | an integration with no contract or version |
| | CONSTRAINT | "reasonable", "sufficient", "fast" with no number |
| | TEMPORAL | "soon", "periodically", "eventually" |
| Quality & operations | ERROR | a capability with no failure case written |
| | RECOVERY | a failure with no degraded or manual path |
| | ASSUMPTION | a dependency or environment taken for granted |
| | STAKEHOLDER | a person who uses the system and is not named |
| | TRACEABILITY | a requirement with no ID, or an ID with no test |

**Gate rule (this skill's default; the owner may change the threshold in the project's contract file):** any question scoring **15 or more** blocks the increment that depends on it until the owner answers. Below 15, it goes in the open-questions list and does not block.

The gate also asks one question of every capability: **which screen will show its result to a person?** If the answer is "none", it is either a system-only capability with a named owner, or an orphan waiting to happen.

---

## 3. The increment — the unit of work

One increment closes one obligation or one journey step. Its order is fixed:

1. **Write the obligation row** — the promise as a sentence that can be false, its source, the case kinds it must survive, the ID.
2. **Write the proof first**, and run it to see it fail. For a primary-quantity write, use the four-property proof of `build-standard.md` §1.
3. **Write the code** in the module that owns the obligation. Name the module's job in its first line.
4. **Run the proof** and paste its output; a passing run that was never red is a written test, not a run test (S8).
5. **Update the surface matrix and the journey grid** for the cells this increment touched (`surface-map.md`, `journey-map.md`).
6. **Update the docs that describe the behaviour** in the same commit (§5).
7. **Update the graph** (`test-tools.md` §1) before finishing the session.
8. **Commit by explicit path**, in reviewable pieces: a new pure module and the rewiring that uses it are two commits.

An increment that skips step 2 has written unowned behaviour, even when the author is the same person who will review it.

---

## 4. Modules and size — the maintainability rules this build must meet

These are the rules every build increment is checked against. They come from the project's code principle; restated here so the build cannot be run without them.

- **Extract jobs, not hubs.** A new module whose input is nearly as large as its output is a hub; moving code into it makes the code worse.
- **Pure before stateful.** Derived values and rules with no framework go in a plain module and get tests with no framework.
- **One job per module,** named in its first line. A folder over ~20 files gets a README map.
- **Comments say why and name the trap.** Never restate the code.
- **Size is debt with a date.** Over ~600 lines the file is named as debt with its next cut written down. Over ~1000 the cut is taken in the same change, not scheduled.
- **Guard tests, not good intentions.** A rule worth keeping has a test that fails when it is broken. `tools/check_structure.py` is the example for this skill's own repo.

---

## 5. The cascade check — after every change

After each increment, check the four cascade types and record each hit in the docs queue (`ddunnock` GUARDRAIL 11, adapted):

- **Terms** — a renamed concept still appears under its old name in a doc, a message, a label or a test name.
- **Links** — a moved or renamed file is still linked from a README, handoff or index.
- **Content** — a behaviour changed and a doc still describes the old behaviour. This is the most common miss, and it fails principle 6 directly.
- **Structure** — a table of contents, a reference index or a navigation list no longer matches the files.

A cascade that is not resolved is written down with its reason. Silence about a known stale doc is how it stops being known.

---

## 6. Idempotent build commands

Every generator, seed, migration helper and scaffolding script must be safe to run at any stage (`ddunnock` GUARDRAIL 13, adapted):

- check the existing state first; skip files that already match the expected content;
- never overwrite a file with manual edits without asking, and back it up if the owner says overwrite;
- never delete existing documentation to make a run succeed;
- read back what was written and refuse to print success for a write that did not land (`SKILL.md` §0.12).

---

## 7. Identifiers — one scheme, used in tests and comments

Pick the scheme once and use it everywhere, because a trace is only as good as the IDs it can follow:

| Prefix | Artefact |
|---|---|
| `OBL-` | obligation row |
| `CAP-` | capability (`C-id`) |
| `SRF-` | surface (`S-id`) |
| `JRN-` | journey |
| `RISK-` | a risk, hazard or failure mode the build is designed against |
| `TEST-` | a proof (test or walk) |
| `ANOM-` | an anomaly found in use or in audit |

Put the obligation ID in the test name and the code comment at the write (`// OBL-014`). A test name without an ID cannot be traced back to a promise.

---

## 8. AI assistance inside the build

When an LLM writes or reviews part of the build, these rules apply (`meddev-ai-assisted-development-governance`, adapted):

- a changed behaviour has a **REQ→TEST link**; "the model says it works" is not evidence;
- for a primary-quantity write, a **reviewer other than the prompt's author** reads the generated patch against the obligation row;
- **no secrets, customer data or production records** go into a prompt or a log; sanitised snippets only;
- the commit or PR says which parts were generated, so the review can weight them.

Delegation of the mechanical parts of the build to cheaper executors follows `agent-deployment.md`; the verification of every delegated result is the increment's step 4, not a separate pass.

---

## 9. The closure gate — when the build is finished (CG1–CG13)

The build is finished when **all** of these hold, and the report lists each one with its count:

| # | Check | Passes when |
|---|---|---|
| CG1 | obligations | every `OBL-` row has a `TEST-` that fails when broken |
| CG2 | capabilities | zero orphans without a declared owner (`surface-map.md` SC1) |
| CG3 | surfaces | zero dead controls; zero audience gaps (SC2, SC3) |
| CG4 | states | every `●` cell renders every state in Σ (SC4) |
| CG5 | journeys | every critical journey grid has verdicts with zero unswept cells (`journey-map.md` §7) |
| CG6 | exits | zero exits without an owner decision, or each one listed as an open decision |
| CG7 | docs | cascade queue empty, or each open item has a written reason (§5) |
| CG8 | graph | every graph in use refreshed after the last code change: `graphify update .`; `cgc index .` or a running watcher (`code-graph-tools.md` §4) |
| CG9 | sweeps | S1–S24 each have a report line with sites (`sweeps/README.md`) |
| CG10 | operator surface | every condition the code cannot resolve shows on a screen the operator already opens (`SKILL.md` §0.11 item 6) |
| CG11 | dependency rules | zero violations and zero cycles from the configured tool; every exception listed with a reason and an owner; C4 arrows match code edges (`design-tools.md` §1–§3) |
| CG12 | decisions | every rule a guard enforces cites an accepted ADR; no accepted ADR without its check (`design-tools.md` §5) |
| CG13 | workflows | every stateful component and multi-step journey has a complete transition table; zero missing transitions, dead states or exit-less states (`design-tools.md` §4) |

A build that closes CG1–CG10 with an open owner decision lists the decision first, with what it blocks. A build that does not close a gate says which gate and which count, and does not say "done".

---

## 10. Relation to the rest of the skill

- Single primary-path write: `build-standard.md` (the four properties, the proof for each).
- Mapping functions to screens: `surface-map.md`. Workflows and their branches: `journey-map.md`.
- How many agents to deploy and which executor takes each step: `agent-deployment.md`.
- Graph, EGM reviews and drift checks used as tests: `test-tools.md`.

---

**Reading receipt: _every gate is a count, never a feeling_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
