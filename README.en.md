# cia — Code Integrity Auditor

**An AI coding skill that audits the *wiring* of a codebase, not its functions: the setting nothing reads, the predicate checked at SELECT and dropped at UPDATE, the catch that fails open, the watchdog that prints "0 problems" while it examined nothing, the state no screen can show. Built on Stafford Beer's Viable System Model. Works on any software; the commerce half lives in the sibling [`ecommerce-cia`](../ecommerce-cia).**

[繁體中文 README](README.md) · Claude Code · Codex · Cursor · any agent that reads `SKILL.md`

## The idea in one paragraph

Linters, type checkers and unit tests inspect one piece at a time. The defects that survive them live *between* pieces: a value frozen at one step and re-read live at another, a control with no consumer, a job whose failure looks identical to its success. This skill first maps every component onto Systems 1–5 of the Viable System Model, then walks the channels between them with 22 sweeps, each of which must name its sites and quote a line from one of them — so a sweep cannot be satisfied by a count. The first law: **nothing dies silently.**

## Use it

```bash
git clone https://github.com/mixocreative/cia ~/.claude/skills/cia      # or ~/.codex/skills/cia
# in any project:
#   "pre-launch audit, Screen tier"      -> the six-step protocol
#   "run tests"                          -> runs the tests, reports counts, offers the audit
#   "something broke"                    -> probe before diagnosis, smallest fix with a test
```

It runs the steps itself (docker up, installs from lockfiles, dev server, browser walk) and asks the owner only for what it truly cannot do — with the exact command written out. Fixes it applies are committed one per finding, with the test that would have caught it; anything irreversible or shared-state is escalated with the patch attached.

## What you get back

A report that opens with five plain lines an owner can act on, then: the VSM map, one line per sweep with sites and a quoted line, the host-capability table, the detector roll call ("is the safety net still looking?"), findings in a fixed format with severity, confidence, boundary and a verification test, and the controls that were proven correct.

## Inside

```
SKILL.md              routing, runtime discovery, six-step protocol, autonomy ladder, sweep index,
                      escalation, plain-language contract, start menu
references/
  sweeps.md           S1–S22 with methods, gradings, report-line formats
  theory.md           the VSM applied to a codebase; Systems 1, 2, 3, 3*, 4, 5
  doctrine.md         evidence grading, context discovery, universal test matrix, domain checklist
  context-templates.md  Blender add-on · e-commerce platform · workflow orchestration
  reporting.md        finding format, severity model, verified controls, final report
tools/sweep-diff.py   shows where this skill's sweeps and ecommerce-cia's have diverged
tests/fixture-service a Python job runner with 10 known defects + answer key; tests/RUNBOOK.md
```

## Provenance

Every sweep was a real defect found under a green suite, a clean analyser and a clean linter, in a shipped project, and written down the day it was found. The commerce-specific lessons went to `ecommerce-cia`; the universal form stayed here. Both skills are cold-tested by fresh agents against fixture projects with answer keys (`tests/RUNS.md`).

License: MIT.
