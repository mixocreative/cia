# Changelog

What changed for someone who uses the skill, newest first. The version is the one in
`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `CITATION.cff`;
`tools/check_structure.py` fails when the three disagree or the newest one has no entry here.
Every scored run behind a doctrine change is in `tests/RUNS.md`.

## [Unreleased]

- `tools/route.py`: the GRAPH line now says which graph answers which question, as
  `code-graph-tools.md` §2 does (CodeGraphContext first for code relationships, graphify first for
  architecture, probe cgc first, refresh a stale `graphify-out/`), and needs two of the six §1
  signals, naming the four it cannot scan. It used to print "graphify, else cgc" on one signal.
  Two guard tests read both rules back from the doctrine.

## [2.5.0] - 2026-11-10

- **S3:** a fallback on a config read that is logged only at debug is HIGH, never MEDIUM.
- **S23:** "the status only moves forward" is a claim the out-of-order cell must prove, not a reason
  to call a replayed update idempotent. Found by the corpus: a Go payment webhook the run had passed.
- **Codex is in the push gate** as its own series, one per reasoning effort (`tools/score.py`,
  `codex_gate`). Measured, not fixed: one Codex run misses one planted row about half the time;
  read two reports (README, "Which agents does it run on?").
- Harness: `--effort` for Codex, `--target`/`--scope` run the corpus through the launcher, a run
  stops its own leftover processes and no one else's (`tests/harness/procs.py`).
- Tools: every tool answers `--help`; an unreadable report path and a mistyped `score.py` flag are
  exit 2 instead of a traceback or a silent pass.
- Corpus re-run on current doctrine: all 8 reachable entries found.

## [2.4.0] - 2026-11-10

- **Both reports are checked files.** An audit writes `cia-audit-report.md`, a build writes
  `cia-build-report.md`, and `tools/audit_report.py` / `tools/build_report.py` name what is missing
  before the reply is sent.
- `tools/inventory.py`: every function, test, config key and write, for a reviewer to answer one by one.
- `tools/untested.py`: the push gate refuses doctrine that has no scored run.
- Gate: the commit under test is judged on every fixture with history; a row one run missed and its
  pair found is variance, a row both missed blocks; one second stage of two more runs.
- Second fixture (`tests/fixture-editor/`, Node) joins the gate.

## [2.3.0] - 2026-11-09

- `tools/route.py`: step 0 of every run, a project scan that prints facts with `path:line`.
- `tools/sweep_leads.py`: S13 no-caller and S21 unrestored-global leads; each gets a finding or a reason.
- `tools/design_check.py`: dependency rules, ADR hygiene and state-transition tables, stdlib only.
- Build mode is cold-tested: `tools/build_report.py` prints the report form and checks it.
- New references: design tools, code-graph tools, companion skills.
- `agents/`: three thin agent briefs (cold auditor, surface mapper, site reviewer).
- Harness: `tests/harness/cold_run.py` starts a cold run with one command; comparison arms
  (`tests/ARMS.md`), EGM reviews (`tests/EGM.md`), and `tools/due.py` to say which are due.

## [2.2.0] - 2026-11-09

- The sweeps file is split into `references/sweeps/` (one receipt covers the folder).
- New references: wiring walk, surface map, journey map, build orchestration, agent deployment,
  test tools.
- `tools/check_structure.py`: nothing loose, nothing missing, S1-S24 once each, file-size debt named.

## [2.1.0] - 2026-10-12

- Evidence discipline (`references/evidence.md`): OBSERVED / INFERRED / UNKNOWN claim tags, the
  authority ladder, the obligation ledger, bounded negatives, contradictions, reverse-trace mode.

## [2.0.0] - 2026-09-13

- The skill becomes a runbook (`SKILL.md`) plus reference files. Sweeps S1-S14 grow to S1-S24,
  depth tiers (Screen / Walk / Full), the plain-language contract, the paired run with
  `ecommerce-cia`, and a planted-defect fixture with an answer key.

## 1.x - 2026-09-10

Single-file skill, v1.0.0 to v1.3.0. See the git tags.
