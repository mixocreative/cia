# EGM reviews of this skill's own documents

One row per Goldfish review run with `python tests/harness/cold_run.py --mode egm --doc <path>
[--reviewer comprehension]` (read-only, from the skill root; the report ends with
`Findings: <blockers>/<majors>/<nits>`). `tools/due.py` reads the newest row per document: a
document that changed by 20 lines or more since that row's commit is due again.

What a Goldfish is for here: the reader who opens one reference with no memory of the rest. It
flags every cross-reference it cannot resolve from that file alone, by design; a reader who arrives
through SKILL.md §0.13 has those. So triage each finding into *fix*, *no change (reason)*, before
the row is written. A review with open findings still resets the clock; the open ones are named.

| Date | Commit | Document | Reviewer | Findings B/M/N | Fixed in | Note |
|---|---|---|---|---|---|---|
| 2026-11-09 | `c8ac18a` | `references/journey-map.md` | comprehension | 22 gaps (not graded) | `c8ac18a` | The 7 internal contradictions fixed (fixed 8-column grid, cell content rules, Unknown vs U, failed walkthrough = ✕ W<n>, non-critical 3-column grid, one reduction line). The 15 others were cross-references. |
| 2026-11-09 | `23d0128` | `references/agent-deployment.md` | comprehension | 0/9/8 | — | No change. The majors are cross-references (S3, §0.12, EGM, CodeGraphContext) a SKILL.md reader has; the "two phrasings" of the delegation threshold are one number, 300 lines, at `:50` and `:56`. First run of the harness's egm mode. |
| 2026-11-09 | `400541f` | `SKILL.md` | comprehension | 0/5/9 | `b058b61`, reverted in `1913add` | Triggered by `tools/due.py` (23 lines since BASELINE). **Fixed, then reverted under the gate** (run AD filed a control; RUNS rows AD, AE), so major 1 is OPEN and due for a retest with two runs: major 1, line 12 put the primary quantity 'in the §3 profile before sweeping' while Step 2 profiles after the sweeps; nit, bare §3 now 'doctrine §3'. **No change, with reasons:** major 2 (VSM Systems not glossed) and the X0 / RUNS / owner nits are what `theory.md` and the references define, and a gloss here would grow the runbook the reading fix just taught runs not to stop at; major 3 (Step 2 is one 350-word sentence) is the sentence carrying the reading rule, and restructuring it is a doctrine change to test on its own, not a tidy-up; major 4 (step budgets vs tier budgets) is real and named as debt: the report's budget line is the tier's (line 170), but the file never says the per-step minutes yield to it, and it should once a run shows the confusion; major 5 (§0.15 trigger) names its subject in `plain-language.md`, and this file's line is the detection rule. $0.22, 4 turns. |

**Backlog, named not hidden.** Every other reference has had no EGM review. `tools/due.py`
measures them from `23d0128` (its BASELINE), so a document becomes due when it is next changed by
20 lines or more, not all at once.
