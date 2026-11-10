# Changelog

What changed for someone who uses the skill, newest first. The version is the one in
`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `CITATION.cff`;
`tools/check_structure.py` fails when the three disagree or the newest one has no entry here.
Every scored run behind a doctrine change is in `tests/RUNS.md`.

## [Unreleased]

- **No doctrine line longer than the Read tool shows.** The Read tool cuts a line at 2,000 characters;
  two long lines are wrapped (text unchanged) and `check_structure.py` check 9 fails a new one. The same
  cut had hidden half of ecommerce-cia's Step 3 reading list.
- The harness names each skill's audit report `<skill>-audit-report.md` and counts it with that skill's own
  checker, so ecommerce-cia's runs are measured the way cia's are.
- **Reading receipts cannot be copied from SKILL.md.** Its example line quoted six real receipts; it now
  shows placeholders, and `tools/receipts.py --gate` fails any receipt phrase found in SKILL.md.
- **SKILL §0.5.3, how a decision's premise is tested:** run the alternative the decision names and see
  whether it does what the sentence says; a cost the design accepts (what a cap leaves out) is the
  decision, not a false premise. One run filed a capped list as 'premise false'; the four runs after
  the rule filed no control. SKILL line 14 also names COMPANIONS, and the gate sentence matches score.py.
- The harness allows `php`, so a PHP fixture can start its own shop.
- `tools/score.py`: a `missed:` tag is read as row ids, so `E8 (noted, not filed)` in one run's note and
  `E8` in its pair's are the same row. Compared as whole strings they shared nothing, and a row both
  runs lost would have passed the gate. A tag that names no row blocks like a missing tag.
- The harness test for the transcript path passes on Linux (CI), not only on Windows.
- `tools/route.py`: the COMPANIONS line no longer lists `.svg` and `<img>` as missing skills (it read
  every backticked token of the kubai-icons row as a skill name). The GRAPH line no longer sends code
  questions to graphify because `cgc` is off PATH: `code-graph-tools.md` §3 says a user-scope install
  may need its full path, so the line says to probe that, or its MCP tools, first.
- `tools/check_structure.py` check 8 (the tools map) has a guard test. `tools/README.md` names who
  calls each tool; `inventory.py` is optional and no SKILL step calls it.
- `tools/untested.py` decodes git output as UTF-8; on a Traditional Chinese Windows a commit message
  with an em dash crashed the gate instead of answering it.
- `tools/README.md` maps every tool by who runs it; `check_structure.py` fails when the map and
  the folder disagree. README's Objections section and gate line are in Chinese too.
- **Companion `kubai-icons`:** a build that needs functional icons, or a screen whose icons are
  missing, placeholders or mixed in style, hands the set to `kubai-icons` (one style from one
  accent; animated or static SVG). `route.py` lists it when installed. The result is re-walked,
  never a closed finding; an icon-only control still needs an accessible name.
- **`code-graph-tools.md` §3, one writer per store:** the embedded CodeGraphContext store takes an
  exclusive lock, so one store per project; a server that will not start falls back to graphify.
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
