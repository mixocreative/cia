# Changelog

What changed for someone who uses the skill, newest first. The version is the one in
`.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `CITATION.cff`;
`tools/check_structure.py` fails when the three disagree or the newest one has no entry here.
Every scored run behind a doctrine change is in `tests/RUNS.md`.
A version ships when `main` carries it: the marketplace entry's source is `./`, so an install or update
takes `main` at that version. A GitHub release is optional, a page for readers, never the delivery; most
versions have none (2.1-2.4, 2.6.x), and the latest release page can trail `main`.

## [Unreleased]

- **`tools/maintainability.py` runs on any directory, not only a checkout**, and says which scope
  it measured. Raised by a Codex cold run of this skill: auditing a throwaway fixture copy, the tool
  refused outright because it enumerates with `git ls-files`, and the run correctly reported "no
  maintainability clearance claimed" rather than a clean result. Inside a worktree it still prefers
  `git ls-files`; outside one it walks the filesystem and states that `.gitignore` cannot be applied,
  so those gaps are candidates for review rather than findings.
- **Enumeration failure is now exit 2, kept distinct from exit 1 "found gaps"**, with `gaps: null`
  in JSON rather than `[]`. `git ls-files` failing *inside* a worktree is a failure, not a cue to
  fall back quietly, and an empty file list never reads as clean.
- **M2's claim is scoped honestly.** It finds a large file that no markdown file MENTIONS; it does
  not check that the mention is a real debt entry with a next cut and a date. Both the tool's output
  and the doctrine now say so, so a clean M2 is not read as "the debt is properly recorded".


## [2.7.0] - 2026-11-14

> **Shipped without its scored fixture runs.** The RUNBOOK requires two cold runs per fixture plus
> two document reviews before a doctrine change is pushed. They could not run here: the harness
> shells out to `claude -p` and the OAuth session had expired. Pushed with `--no-verify` at the
> owner's explicit instruction. `tests/RUNS.md` carries the outstanding block and the commands to
> clear it, and the gate will keep refusing the next push until real rows exist. `check_structure`,
> `check_key_lines`, `zh_check` and `receipts` all passed.


- **The owner's code principle is now part of every audit, not only of a build**
  (`references/maintainability.md`, new). It was already written down -- in `build-orchestration.md`
  §4 -- but only on the BUILD path, so an audit could report a repo green while a 43-file folder had
  no README map and six files sat over a thousand lines with no seam written down. Measured on three
  real repos the day this shipped: 10 missing folder maps and 13 files past the cut limit, none of
  them visible to any sweep. §4 now points at the one copy instead of restating the rules, because
  two copies of a principle is how a principle starts contradicting itself.
- **`tools/maintainability.py <repo-root>` is the instrument**, and works on any git repo: M1 folder
  maps past ~20 files, M2 size debt (over ~600 named, over ~1000 cut), M3 the module's job said in
  its first lines, M4 links in LIVING docs that resolve. Vendored and generated trees are excluded;
  a folder is exempt from M1 by its CONTENTS, never by its name, after the first run exempted
  `src/core/assets` for having "assets" in the path. Dated documents are skipped by M4 on purpose: a
  record corrected silently stops being a record.
- **The tool states the two rules it cannot see,** in its own output: whether a module is a hub
  rather than a job, and whether a comment says why rather than what. Both need a reader. A clean
  M1-M4 line does not establish that code is well modularised, and report line `2i.` is refused
  without the paths a human actually judged -- a blind instrument reporting like a seeing one is
  S20 filed against the auditor.


## [2.6.2] - 2026-11-10

- **The Stop hook runs where there is no Git Bash.** Claude Code runs hook commands in PowerShell on Windows
  without Git Bash, where 2.6.1's `if ...; then ...; fi` was a syntax error on every Stop. The command is now
  `python3 <hook>; python <hook>; exit 0`, which bash, sh and PowerShell all parse: whichever interpreter runs
  first reads the payload, the second reads nothing and stays silent, and `exit 0` keeps a missing `python`
  (stock macOS) from turning the answer into exit 127, which Claude Code would discard (Fable's review). Shown end to end: Claude Code ran it through
  PowerShell 7.6 (a marker the hook wrote) and it blocked a failing report. Tests run the shipped command
  under `sh` and PowerShell; CI runs them on Linux, macOS and Windows. Windows' own `python3` placeholder
  (App Installer's `AppInstallerPythonRedirector.exe`, run through its alias) was measured: it writes its
  message to stderr only, leaves stdin unread and exits non-zero, and with python.org's `python` behind it
  the shipped command printed the block and exited 0 under bash, PowerShell 7 and Windows PowerShell 5.1.
  It matters: any text on stdout beside the JSON makes Claude Code read the answer as plain text, no block.
- **A hook that cannot run says so.** With the command ending `exit 0`, a crash would have turned the guard
  off silently; it is now shown to the user as a `systemMessage` (never a block), and only in a session whose
  turn wrote a report, because the checker is loaded only then.
- RUNBOOK's plugin smoke step also runs once with the hook forced to `"shell": "powershell"`.

## [2.6.1] - 2026-11-10

- **The plugin loads again.** `plugin.json` listed `./agents`, a folder; Claude Code's manifest schema wants
  each agents entry to be a `.md` file and refused the whole plugin ("agents.0: must end with .md"), so no
  agent, skill or hook of an install loaded. Each agent file is listed, and the guard test checks that.
- **The Stop hook guards a report written outside the working directory:** it also checks every file named
  `cia-audit-report.md` that any tool call in the turn named (a Write, an Edit, a Bash redirect); a malformed
  tool input is skipped, never an error.
- **The hook command survives a `python3` that is not Python** (the Windows Store stub): it probes
  `python3 -c ''` with stdin closed, then runs one interpreter; a test runs the shipped command under `sh`
  with a stub that eats stdin.
- RUNBOOK: a plugin smoke step before every release, the check that found the two above.

## [2.6.0] - 2026-11-10

- **A Stop hook holds Step 6.** The plugin ships `hooks/hooks.json`: a session that wrote `cia-audit-report.md`
  cannot finish while `tools/audit_report.py` fails on it; the hook hands back the MISSING lines once, and a
  retry is never blocked. About half the cold runs had replied past a failing checker. The harness runs hermetic
  (no user-level settings) and passes the hook in, so runs measure what a plugin user gets.
  Fixed before release (Fable's review): the report name is the literal `cia-audit-report.md`, not taken from
  the install folder (an installed plugin's folder is its version, and the hook never fired there); the window
  is the turn now ending, read from the transcript's timestamps, not the file's `st_ctime` (which moves on
  every append on macOS and Linux), so a later turn or a resumed session is never blocked; a broken install
  exits quietly; the command tries `python3`, then `python`.
- **The gate's second stage is checked for eligibility:** four runs on a commit are read only when its first
  two were within one row of the floor. RUNBOOK step 4 writes down two scoring rulings: a row folded into a
  neighbouring finding is a hit, a row named only on a sweep line or in a ledger is a miss.
- The harness keeps a hooked run's final reply when its report file was collected; the longest earlier reply
  is the draft the hook blocked.
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
