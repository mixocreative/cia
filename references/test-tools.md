# Test tools — graphify for the blast radius, EGM for the cold read, and the gates a test must pass

> Job of this file: decide **what to test for a change** and **how the test is proved to be real**, using two tools the owner already runs: **graphify** (a code graph, for finding what a change touches) and **EGM — Elephant-Goldfish Model** (Google, Apache-2.0; deep-context Elephant sessions draft specs, zero-context Goldfish subagents stress-test them). Neither replaces a run. Both make the set of things to run smaller and better aimed.
>
> Installed on this machine: the `graphify` CLI (`~/.local/bin/graphify`) and the EGM plugin (`~/.claude/plugins/marketplaces/egm`, commands `/egm:egm-review`, `/egm:egm-drift-report`, `/egm:egm-bootstrap`, and the agents `egm:egm-comprehension`, `egm:egm-zoom-out`, `egm:egm-implementation-readiness`, `egm:egm-design`, `egm:egm-structural`, `egm:egm-style`, `egm:egm-codebase-details`). Probe before relying on them (§5).

---

## 1. graphify — finding what a change touches

Use the graph before reading files. It answers the structural question for a few hundred tokens where a wide read costs tens of thousands.

**Choose the graph by the question** (`code-graph-tools.md` §2): once CodeGraphContext is in place, callers and paths (steps 2–3 of the recipe below) go to it, and graphify supplies the architectural context. Neither graph outranks the code (§2.3). **Build or refresh.** `graphify update .` in the project root; for CodeGraphContext, `cgc index .` (or a running `cgc watch .`), after the checks in `code-graph-tools.md` §3. It writes `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`, `graph.html`). Run it before finishing any session that changed code (the user's standing rule). `graphify-out/` is generated and is not committed (`.gitignore`).

**Ask it, bounded.** Every query has a token budget; the default (about 2000 tokens) truncates large answers, and a truncated answer is marked `TRUNCATED` and is not complete (`SKILL.md` §0.12 rule 5). Pass `--budget` when the answer is big, or narrow the query.

| Question | Command |
|---|---|
| What is near this symbol — callers, callees, the file it lives in | `graphify explain "<symbol>"` (add `--all` for every edge) |
| Which code connects an entry point to a primary-quantity write | `graphify path "<entry>" "<sink>"` (add `--undirected` when edge direction is unreliable) |
| Which files and communities mention a concept | `graphify query "<concept>" --budget <n>` |
| Is a count from the graph safe to report (same-endpoint edges can collapse) | `graphify diagnose multigraph` |

**How to read the answer.** Each edge carries a tag. An `[EXTRACTED]` edge was read from source by the extractor and is a code fact; an `INFERRED` edge is a hypothesis about how two things relate. Treat `INFERRED` the way `evidence.md` §E1 treats any claim: it is a lead until a read of the cited line confirms it. The graph is a map of the code, not evidence about the behaviour.

**The blast-radius recipe for a change:**

1. Name the symbols the diff touches (from the diff, not from memory).
2. `graphify explain` each one → its callers and callees.
3. `graphify path` from every entry point (route, job, consumer) to every primary-quantity write the callers reach.
4. Every node on those paths is a candidate test target. Map each to its row in `surface-map.md` (capability) and `journey-map.md` (journey).
5. A target with no test edge, or with a test that does not exercise the changed line, is a gap — report it, don't assume it is covered.

---

## 2. EGM — the cold read of specs, journeys and test plans

The Elephant-Goldfish idea: the author's own context hides what is missing. A Goldfish is a subagent that starts with **no context** and must answer from the document alone. If it cannot act on the document, the document is not finished, however clear it looks to its author. That is the same mechanism as this skill's cold runs (`tests/RUNBOOK.md`), applied to the specification.

Use it on four artefacts:

| Artefact | EGM tool | What the Goldfish is asked |
|---|---|---|
| A journey or a spec section (`journey-map.md`) | `/egm:egm-review <doc>` — the multi-stage pipeline (Zoom Out → Comprehension → Critic → Readiness) | "Can you implement and test this journey using only this text? What is missing?" |
| The surface matrix or a test plan | `/egm:egm-review` with the readiness and structural agents | "Which cell or case has no stated outcome?" |
| Code against its spec (drift) | `/egm:egm-drift-report` — an AST scanner comparing checked-in design documents with live code | "Does the code still do what the document says?" |
| Folder README maps (folders over ~20 files, `build-orchestration.md` §4) | `/egm:egm-bootstrap` — generates directory READMEs with sentinel blocks | keeps human-written sections; regenerate the rest |

**Grade what comes back under the evidence rules.** A Goldfish finding about a document is a finding about the document's wording and completeness; grade it as such (`reporting.md` §9). A Goldfish PASS is **not** a test pass: it says the document is understandable, not that the code behaves (S8 applied to reviews). Record it as `●(read)` in the journey grid, never as `●`.

**Drift as a liveness check.** A drift report that scanned zero documents or zero code files looks identical to a clean one. Its report must print how many documents and files it scanned; a zero there is a finding (S20, the safety net that cannot see).

---

## 3. The selection algorithm — which tests a change must pass

For each change, in order:

1. **Blast radius** (§1) → the capabilities and surfaces the change reaches.
2. **Map to the matrix** (`surface-map.md`) and the journeys (`journey-map.md`) → the cells and grid rows that depend on those capabilities.
3. **List the proof each row needs**, by kind:
   - obligation → a guard test that fails when the promise is broken (`build-orchestration.md` §3 step 2);
   - state branch → a test or fixture that returns that state (C4);
   - journey cell → an automated test or a state-delta walk (`browser-walks.md` §12); a cold read alone is `●(read)`;
   - document line → the EGM pass on the document, and the drift report.
4. **Run the fast suite**, then the targeted tests from step 3. Record the command, the counts and the file list.
5. **Log which proof closed which row**, so a reader can see the mapping from change to evidence. A row with no proof stays open, and the report says so.

A change whose blast radius is empty in graphify is a change graphify does not model (generated code, dynamic dispatch, a config-driven path). Say so; do not report "no impact".

---

## 4. The gates a test must pass to count

These are the rules that stop a green run from hiding a broken check. Each is a sweep elsewhere in this skill; they are listed here because they decide what counts as a test result.

| Gate | Rule | Sweep |
|---|---|---|
| Skipped is not green | a skipped test is an unverified claim; the report counts it separately | S7 |
| Written is not run | a test file that never ran in the suite is not evidence | S8 |
| A test must be able to fail | it is shown failing on the broken code, or a fault is injected that makes it fail | S21 |
| The suite is an instrument | an assertion that something is empty proves nothing until something proves it can be non-empty | S21 |
| The fixture is not the authority | a fake that agrees with the parser proves only that the parser agrees with itself | S24 |
| The safety net reports its own liveness | a checker prints how much it examined; zero examined is not clean | S20 |

---

## 5. Probe before use

Before relying on either tool in a run, check it answers — rung 3 of the self-service ladder (`SKILL.md` §0.8) if it does not:

- graphify: `graphify --help` prints usage; `graphify query --help` prints the budget option; `graphify-out/graph.json` exists and is newer than the last code change. If the graph is stale, run `graphify update .` first.
- EGM: the plugin directory `~/.claude/plugins/marketplaces/egm` exists and `/egm:egm-review` is listed. If it is missing, say so in the report and fall back to a manual cold read by a fresh subagent with the same brief; do not claim the EGM pass ran.

State which tool ran, and its version or path, in the report's rung line (`agent-deployment.md` §8).

---

## 6. Report line

```
TESTS — change touches C capabilities (graph: E extracted edges, I inferred, path-checked P entry→sink); targets T; with proof G; gaps without proof U;
        EGM passes run D (documents), drift scanned Fd docs / Fc code files; gates: skipped-unverified K, written-not-run W.
        sites: <path:line per gap>; the command and counts of the fast suite, verbatim.
```
