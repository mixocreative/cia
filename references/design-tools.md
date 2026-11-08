# Design tools — architecture maps, feature slices, dependency rules, state machines, decision records

> Job of this file: the five design methods a build is checked against, what each one solves, how the audit turns each into a check that can fail, and where each one sits in the build order. Built on `build-orchestration.md` (the closure gate) and `journey-map.md` (the workflows the state machines must cover).
>
> Priorities are the owner's (table below). The examples are for the project being audited; this skill's own repository has none of these layers.

| Method / tool | What it solves | Priority | Adopt by |
|---|---|---|---|
| C4 architecture maps | shows how major systems and components connect | Essential | the first increment |
| Feature-Sliced Design (FSD) | organises code by feature and responsibility | Essential for UI | the second feature, before code grows around it |
| Dependency Cruiser (and equivalents) | detects circular imports and forbidden dependencies | Essential | the first CI run |
| State machines | controls complicated UI workflows and transitions | High | before any multi-step workflow is coded |
| Architecture Decision Records (ADR) | preserves why important design decisions were made | High | with the decision, never after it |

---

## 1. C4 — architecture maps, checked against the code

**What it solves.** A system whose parts nobody can draw is a system nobody can change safely. C4 gives four zoom levels: **Context** (the system and the people and outside systems around it), **Containers** (deployable units: app, API, worker, database), **Components** (the modules inside one container), **Code** (classes and functions, generated, not drawn by hand).

**The check.** A map is a claim about the code, so it is tested against the code (the graph is the instrument, `test-tools.md` §1):

- every **box** on the map has a code location (`path:line` or a directory) — a box with none is a planned component, and the report says so;
- every **arrow** has a call or import the code-relationship graph finds (CodeGraphContext once in place, else `graphify path`; `code-graph-tools.md` §2). An arrow with no edge is stale;
- every **code edge** that crosses a container or component boundary appears as an arrow. A missing arrow is a hidden coupling, and it is the finding.

**Sweep it with.** S11 (boundary contract), S15 (four-corner walk), S13 (orphan components). The report line:

```
C4 — containers M (mapped), N (in code); components K mapped, J with code; arrows A mapped, E with an edge, hidden couplings H; sites: <boxes/arrows with no evidence>.
```

**Keep the map honest.** Generate the Component level from the graph where the stack allows it, and keep the human-written Context level under review. A hand-drawn map that is never regenerated is a map of the author's intent on the day it was drawn.

---

## 2. Feature-Sliced Design — organise UI code by feature and responsibility

**What it solves.** UI code grows by page and by component until one change touches six folders. FSD organises the frontend into layers, slices and segments, with one rule: **a layer may import only from the layers below it**, and slices on the same layer do not import each other.

Layers, from the top: `app` (startup, providers, routing) · `processes` (multi-page flows, if used) · `pages` · `widgets` · `features` (one user action) · `entities` (one business object) · `shared` (no business meaning). Each slice holds segments: `ui`, `model` (state and rules), `api`, `lib`, `config`.

**The check.** An upward import (a `features` file importing from `pages`) or a sideways import (`features/cart` importing `features/checkout`) is a violation. Enforce it mechanically with the dependency rules in §3, not by review. Report the violations with their sites; the count is zero or the gate fails.

**Where it does not apply.** A back end or a CLI has the same problem under other names: a layered architecture, or hexagonal ports and adapters. The rule is the same — dependencies point one way — and the check in §3 is written for the stack, not for FSD. FSD is named here because the owner's stack is UI-heavy.

**Sweep it with.** S5 (a control that does not reach its consumer), S13 (orphan features), S22 (surfaces) — FSD makes those checks cheaper, because each feature has one place to be found.

---

## 3. Dependency rules — circular imports and forbidden dependencies

**What it solves.** Circular imports and forbidden dependencies (a `shared` module that imports a feature; a `domain` package that imports the database driver) do not fail a build. They fail six months later, when a change cannot be made without touching everything. A rule that is not checked is a wish.

**The tool, by stack.** Pick the one that matches the stack and check that it is installed; do not assume the name.

| Stack | Tool |
|---|---|
| JavaScript / TypeScript | dependency-cruiser (`depcruise`), config `.dependency-cruiser.*` |
| Python | import-linter (`importlinter` contracts in `pyproject.toml`) |
| Java / Kotlin | ArchUnit (tests) |
| Go | `depguard` rules in the lint configuration |
| Rust | `cargo-modules` for the dependency graph, plus a test that asserts the allowed edges |

**The rule set, written down before the first violation.** At minimum:

1. no cycles between modules (`no-circular`);
2. each layer or package imports only what its layer allows (the FSD rule in §2, or the stack's equivalent);
3. the domain or core does not import infrastructure;
4. a rule that must be broken has an exception with a reason and an owner — silence about a known breach is the finding (code principle 8: debt not taken is written down; `build-orchestration.md` §5).

**The check.** Run it as a guard test in CI, not as a manual review. The output is a count with sites; zero violations and zero cycles is the pass. A test that prints violations and exits 0 is a vacuous pass (S7/S21 applied to the rule itself): the run must fail on a planted violation, once, to show it can.

**Run it.** `python tools/design_check.py deps <root> --rules design-rules.json` prints the cycles and violations with their sites, and exits 1 on any. Its UNRESOLVED count names the aliased imports it did not check.

**Sweep it with.** S13 and S17 (a rule enforced outside the system is a label), S21 (a check that cannot fail).

---

## 4. State machines — complicated UI workflows and transitions

**What it solves.** A screen with a wizard, a save button, a retry and a conflict has states that nobody wrote down. The bugs are the transitions nobody planned: a double submit, a retry from a state that cannot retry, a success message from an error state.

**The method.** For each interactive component and each multi-step workflow (`journey-map.md` steps):

1. list the **states** (idle, editing, submitting, submitted, failed, conflict, read-only, …) and mark the terminal and the safe states;
2. list the **events** (submit, retry, cancel, timeout, server-error, conflict-detected, …);
3. write the **transition table**: every (state, event) pair is either a transition to a named state or explicitly ignored, with a reason. Guards are written as conditions, not comments.

**The checks.**

- a (state, event) pair with neither a transition nor an explicit ignore → a missing transition, a finding;
- a state no transition reaches → dead, a finding (unless it is the initial state);
- a non-terminal state with no exit the person can take → the trap T1 in `journey-map.md`;
- a transition with no test that fails when it is broken → S21 and S8;
- a machine in code that differs from the table in the docs → drift (`test-tools.md` §2, the EGM drift report).

The state-delta ladder (`browser-walks.md` §12) observes the transitions on screen; the table is the spec it is checked against. `meddev-state-machines` (MIT) adds the safe-state and timeout rules for devices and other safety-relevant flows.

**Run it.** `python tools/design_check.py states <table.json>` checks the table: missing cells, unreachable states, exit-less states.

**Walk it.** The table is also the test plan: generate one Playwright (or CLI) walk per transition row from the table file — drive the event from the state, assert the target state's marker on screen (`browser-walks.md` §12) — and write one line per walked transition (`state event target`) to a log. `python tools/design_check.py states <table.json> --walked <log>` then fails on every row with no walk and on every walk the table does not contain, and prints `transitions walked W/T`. A walk generated from the table cannot test a transition the table omits, so the completeness check runs first. Do not adopt a statechart library for this: the table is already the model, and a proof that re-implements its subject proves the re-implementation (S21).

**Sweep it with.** S16 (every non-terminal state has a queue or an exit), S22 (step × outcome × audience), S23 (arrival order).

---

## 5. Architecture Decision Records — why the design is what it is

**What it solves.** Six months later nobody knows why the queue is Postgres and not Redis, or why the FSD rule has an exception. Without the reason, the next person either removes the rule or keeps a bad decision because they cannot see its cost.

**When to write one.** At the moment of the decision, for any decision that: chooses between alternatives; adds or removes a layer, dependency or external service; creates a rule that a check enforces (§3); or changes an owner decision recorded earlier. A decision made without a record is not made yet — it is a habit.

**The format** (Nygard style; `docs/adr/NNNN-short-title.md`):

```
# NNNN — Title
Status: proposed | accepted | superseded by NNNN | deprecated
Date: YYYY-MM-DD
Context: the forces, the constraints, what was known then.
Decision: what was chosen, stated so it can be checked.
Consequences: what becomes easier, what becomes harder, what is now enforced where (the check's path).
```

**The checks.**

- every rule enforced by a guard test (§3, §4) cites its ADR in the test or the rule's config; a rule with no ADR is an unexplained rule, graded as debt;
- an ADR whose status says accepted but whose check is absent is a decision nobody enforces;
- a code path that contradicts an accepted ADR is **escalated, not fixed** (`SKILL.md` §0.5 item 3): the owner decides whether the ADR or the code is wrong.

**Run it.** `python tools/design_check.py adr docs/adr` checks each record's fields, status and supersedes links.

**Sweep it with.** S5, S13 (the decision that was never built), S18 (the authority document is the ADR when one exists).

---

## 6. Build order and where each method enters the closure gate

Adopt in this order, because each one assumes the one before:

| Step | Method | Gate it satisfies |
|---|---|---|
| 1 | ADR for the stack and the first structural choices | CG12 (decisions recorded) |
| 2 | C4 map of containers and components | CG11 (dependency map exists to check against) |
| 3 | Dependency rules in CI, FSD layers for UI | CG11 (zero violations, zero cycles) |
| 4 | State machine tables before each multi-step workflow is coded | CG13 (every transition table complete) |

The three gates below join `build-orchestration.md` §9; they are numbered after CG10 so existing references stay valid:

| # | Check | Passes when |
|---|---|---|
| CG11 | dependency rules | zero violations and zero cycles from the configured tool; every exception listed with a reason and an owner; C4 arrows match code edges (§1) |
| CG12 | decisions | every rule a guard enforces cites an accepted ADR; no accepted ADR without its check |
| CG13 | workflows | every stateful component and multi-step journey has a complete transition table; zero missing transitions, dead states or exit-less states |

---

## 7. Report line

```
DESIGN — C4 containers M/N, arrows A/E, hidden couplings H; FSD violations V; dependency violations D, cycles Y, exceptions X (owned O);
         ADRs cited by enforced rules R/T, contradicting code K (escalated); state machines M_t with missing transitions Z, dead states Q, exit-less E.
         sites: <path:line per finding>; the configured tool's command and exit count, verbatim.
```

## 8. Sources and limits

- C4: Simon Brown's model (the four levels are his; the arrow-to-edge check is this skill's).
- FSD: the public Feature-Sliced Design methodology; the layer order is its rule.
- Dependency tools: named as they are commonly packaged; verify the name and version at adoption.
- ADR: Michael Nygard's format.
- State machines: the table method and the checks are this skill's; the safe-state and timeout rules come from `meddev-state-machines` (MIT).
- None of these tools is run by this skill's own repository; the checks apply to the audited project.

---

**Reading receipt: _the map is a claim the graph can disprove_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
