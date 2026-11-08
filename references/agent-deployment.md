# Agent deployment — deciding, for each step, which executor does it

> Job of this file: when the audit or a build starts, decide **who runs each step** — a deterministic tool, the graph, a local model, a cheap subagent, the main model, or a cold reviewer — so that the bulky reading is done cheaply and the judgment stays with the model that can carry it. Every delegated result is verified before it enters a report.
>
> Its rules come from the user's global standing rules (judgment stays with the main model; bulky mechanical steps go to a local model or the cheapest capable subagent; every delegated result is verified) and from the `token-economy-delegation` skill, which holds the probe and the Ollama procedure. Routing and selection ideas adapted from `meddev-agent-skills` `AGENT_INTEGRATION.md` (rules → keywords → tie-break; prerequisite closure; logged injections). Both `token-economy-delegation` and this file apply; this file is the audit-specific decision table.

---

## 1. The principle

**Judgment stays with the main model. Bulk stays out of it.**

Judgment: grading severity, deciding whether a finding is confirmed, choosing fix-versus-ask, escalating, writing the report, deciding what a PASS means. These depend on the whole conversation and on evidence the reader must hold together. They are never delegated.

Bulk: reading large files, enumerating call sites, listing every conditional, comparing two long lists, scanning logs, running the same check over forty files. These produce a lot of text whose conclusion is a short list. They are delegated, and the delegate returns the list, not the text.

---

## 2. The decision ladder — the cheapest executor that answers

Walk down the ladder. Stop at the first rung that can answer the question with the evidence it needs.

| Rung | Executor | Use it for | Token cost to the main context |
|---|---|---|---|
| 0 | **Deterministic tool** — grep, the test runner, the linter, `tools/check_structure.py`, `tools/sweep-diff.py` | any question a command can answer exactly: does this symbol exist, do the tests pass, does the file still parse | none beyond the output line |
| 1 | **Graph** — `graphify query`, `path`, `explain`, or GitNexus when the project passes the complexity signals in `code-graph-tools.md` | structural questions: who calls X, what sits between an entry point and a sink, what is the blast radius of a change | the query's bounded answer (`test-tools.md` §1) |
| 2 | **Local model** (Ollama) — only after the probe in `token-economy-delegation` succeeds | bulky mechanical text work: summarising a long log, reformatting a table, first-pass tagging of many short items | the local answer; **untrusted until verified** |
| 3 | **Explore subagent** — read-only fan-out search | "find every place that does X" across many directories, when the answer is a list of `path:line` | the list only |
| 4 | **Cheapest capable subagent** (Haiku, then Sonnet if Haiku misses) | a bounded per-file review against an explicit checklist — for example, classify each catch block in eight files by the S3 posture | the verdict table |
| 5 | **Main model** | judgment; reasoning across files; grading; confirmation; the final report | everything — keep it small by using rungs 0–4 first |
| 6 | **Cold reviewer** — a fresh context with no memory of the author (EGM Goldfish, or a cold audit run) | "can someone who has only this document act on it?"; a second opinion on a finding | the reviewer's verdict list |

Two rules sit above the ladder:

- **A cheaper rung never grades.** Rungs 0–4 return evidence. The main model (or the cold reviewer for a judgement about wording) decides what the evidence means.
- **Start at the top only when the answer is exact.** Do not use a grep to answer a question that needs reading, and do not read a file to answer a question a grep answers.

---

## 3. When to deploy, and when not to

Deploy a delegate when **all** of these hold:

- the reading is bulk — roughly 300 lines or more, or more than three files — or the same check repeats across many sites;
- the output can be a checklist of `path:line` items with a verdict from a fixed set;
- the answer does not need the rest of this conversation.

Do **not** deploy a delegate when:

- the whole job is under about 300 lines of reading: the cost of briefing and verifying exceeds the cost of reading it;
- the output decides a severity, a confirmation or an escalation;
- the brief would have to paste the main model's conclusion in order to be understood ("based on the findings…" is not a brief).

The threshold is a default. Record the choice and the reason in the report's rung line, so the next run can judge whether it was right.

---

## 4. The delegation contract

Every brief names:

1. **Goal** — one sentence, and what done looks like.
2. **Scope** — the exact files or directories, and what is outside it.
3. **Ruled out** — what has already been checked and must not be re-checked.
4. **Output schema** — a table with fixed columns: `site` (`path:line`), `verdict` (from a closed set), `quoted` (the one line that justifies the verdict, verbatim).
5. **Stop condition** — when to stop (all files read; first N hits; budget reached) and what to return if it stops early (`TRUNCATED`, with what was not read).

A result without the quoted line is not a result. An output with `TRUNCATED` is not counted as complete (`SKILL.md` §0.12 rule 5).

---

## 5. Verification — before any delegated result enters a report

Verification depends on what the result claims:

| Claim | Verify |
|---|---|
| "X is at `path:line`" | open the line and read it; a wrong line is a wrong finding |
| "0 findings in these N sites" | the sites list is complete (count the files the brief named against the files the delegate returned) and each site has a quoted line — a count alone is the vacuous pass S8 names |
| "this is a bug" (positive finding) | read the cited code yourself and confirm the invariant (`reporting.md` §9 confidence rules); a delegate's positive finding is a lead until read |
| "PASS" for a runtime behaviour | never accepted from reading; it needs a run (`evidence.md` §E1) |

**Sample rate.** Read every positive finding a delegate returns. For negative results ("no problem here"), read a sample — at least the sites a rule would most likely fail (the catch blocks, the handlers, the branches) — and widen the sample if any sample is wrong.

---

## 6. Parallelism and session boundaries

- Independent sweeps and independent directories fan out in parallel. Dependent steps run in order.
- Keep the number of simultaneous delegates small. Each one costs a full brief and a full return; many small fan-outs cost more than one well-scoped one.
- A **separate session** is for a task that outlives this one and that the user asks to run apart. Work that feeds the current answer stays in the current session, as a delegate or inline.

---

## 7. Choosing which reference files to load

The protocol already routes by file (`SKILL.md` §0.13). Apply the same discipline to the executors: a delegate loads only the reference sections its checklist names, not the whole skill. The rules layer is the trigger table in §0.13; the keyword layer is the `When to apply` line of each reference; when both leave two candidates, the main model decides — it does not guess with a second model.

Prerequisites are loaded first. `build-orchestration.md` needs `build-standard.md` and `evidence.md` (the obligation ledger) before it can be applied; a delegate briefed on the orchestration without those is briefed on half of it.

---

## 8. Recording the choice

The Step 6 report carries one line per phase:

```
EXECUTORS — phase <name>: <rung> <executor> for <what>; reason: <why this rung>; verified: <how many results read / sampled>; returned TRUNCATED: <n>.
```

This line is how the next run learns which rungs paid for themselves. A phase where every delegated result was wrong is a finding about the rung, and it is written down.

---

## 9. Measures

Track these across runs in `tests/RUNS.md` (or the project's handoff), not as a guess:

- share of delegated positive findings confirmed on read (low = the brief or the rung is wrong);
- share of verified-sample negatives that turned out wrong (high = widen the sample);
- tokens in the main context per phase, against the same phase run with everything inline.
