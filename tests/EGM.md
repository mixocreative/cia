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

**Backlog, named not hidden.** Every other reference has had no EGM review. `tools/due.py`
measures them from `23d0128` (its BASELINE), so a document becomes due when it is next changed by
20 lines or more, not all at once.
