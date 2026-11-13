# The code principle — the maintainability audit

> The owner's standing instruction, in their words, and the authority for everything below:
> *"all documents updated, all readme updated, and code base is in best shape, well organized,
> human readable, maintainable friendly, and well modulized."* Stated 2026-11-14, as a principle
> for **every repo**, not one project.

This is the one part of the audit that is not about a defect a user can hit today. It is about
the defect the **next person** hits: they cannot find the module, so they write a second one; the
doc says the old behaviour, so they trust it; the file is 1,500 lines, so they add to the end.
Every one of those is a future bug with the author's name on it, and none of them shows up in a
green suite — which is exactly the shape of thing this skill exists to catch.

**Where this runs.** Step 2 of §0.6, with the sweeps, and its own line in the Step 6 report. In
build mode it is `build-orchestration.md` §4, which points here rather than restating the rules —
two copies of a principle is how a principle starts contradicting itself.

**What it is NOT.** Not style taste. Not line-count theatre. Not a mandate to split a file that
reads well. Every rule below has a named cost to the next reader, and a rule whose cost you
cannot name on the file in front of you does not apply to it.

---

## 1. The nine decision rules, in the order the decisions come up

The first three are the load-bearing ones; they decide whether code moves at all.

1. **A module is clean when its output is narrower than its input.** Count the fields before
   extracting. A new module that needs nearly as much handed in as it hands back is a *hub*, not
   a job, and moving code into it makes the codebase worse while looking like progress.
   **Extract jobs, not hubs.**
2. **Pure before stateful.** Derived values and rules that need no framework go in a plain module
   and are tested without one. An extraction that buys a test for a rule nobody was testing is
   worth more than an extraction that only shortens a file.
3. **One job per module,** named in its first line. A folder past ~20 files gets a README map — a
   folder of 69 files and no map is a navigation bug, not a preference.
4. **Comments say WHY and name the trap.** Never restate the code. Put the comment where the
   mistake would be made, so the next person meets it before making it.
5. **Size is debt with a date.** Over ~600 lines the file is named as debt with its next cut
   written down. Over ~1000 the cut is taken, not named.
6. **Docs move with the code, in the same commit** — the folder README, the design doc, the
   handoff. A commit that changes behaviour and leaves the docs describing the old behaviour is
   unfinished, not finished-with-a-follow-up.
7. **Guard tests, not good intentions.** A rule worth keeping gets a test that fails when it is
   broken: boundary tests, allowlists with reasons, pure-function tests.
8. **Debt not taken is written down with the reason.** Silence about a known rough edge is how it
   stops being known.
9. **Commit by explicit path, in increments a person can review.** A new pure module and the
   rewiring that uses it are two commits, not one.

---

## 2. Four rules a tool measures, two a tool cannot

`tools/maintainability.py <repo-root>` measures the four mechanical rules on any git repo. It
excludes vendored and generated trees, and exempts a folder from M1 when its **contents** are
mostly data — keyed on contents, never on the folder's name, because `src/core/assets` is code
about assets and `tests/fixtures` is a data store.

| ID | Rule | What the gap costs the next reader |
|---|---|---|
| **M1** | a folder past ~20 files has a README map | they cannot find the module, so they write a second one |
| **M2** | past ~600 lines the file is named as debt; past ~1000 the cut is taken | they add to the end, because there is no stated seam |
| **M3** | a source module says its job in its first lines | they must read the whole file to learn whether it is the right one |
| **M4** | a link in a **living** doc resolves | they follow it, find nothing, and stop trusting the docs |

**M4 skips dated documents on purpose.** A dated file is a record of a moment: it is superseded by
a newer dated file, or corrected in place *with the correction marked*. Silently repointing a
link inside a record is how a record stops being a record, so the tool does not ask for it.

**Rules 1, 2 and 4 of §1 are not measurable and the tool says so in its own output.** Whether a
module is a hub, and whether a comment says why rather than what, need a reader. A run that
prints M1–M4 clean has **not** established that the code is well modularised — claiming it has is
a blind instrument reporting like a seeing one, which is S20 filed against the auditor. Judge
those three by hand, on the files the run actually touched, and say which files you judged.

---

## 3. The cascade check — what a behaviour change drags with it

After any change, four cascades, each a way a doc goes stale (`build-orchestration.md` §5):

- **Terms** — a renamed concept still appears under its old name in a doc, a message, a label or
  a test name.
- **Links** — a moved file is still linked from a README, a handoff or an index. This is M4.
- **Content** — behaviour changed and a doc still describes the old behaviour. **The most common
  miss, and it fails rule 6 directly.** No tool finds it: it needs the diff read against the doc.
- **Structure** — a table of contents, a reference index or a folder map no longer matches the
  files.

A cascade left unresolved is written down with its reason (rule 8). An unresolved cascade that is
*also* unwritten is the finding.

---

## 4. Grading

Graded on `reporting.md` §10 like any other finding, with the ceiling this class carries:

| Situation | Grade |
|---|---|
| a living doc states behaviour the code no longer has, on a **primary path** | **MEDIUM** — the next person acts on it; a wrong map is worse than no map |
| a folder past the limit with no map; a file past the cut limit with no seam written down | **LOW** |
| M3 or M4 alone | **LOW** |
| any of the above where the doc is dated, and marked as a record | **not a finding** — see §2 |

This class never reaches HIGH on its own. It is also never dropped for being LOW: the owner's
instruction above makes it part of the definition of done, and a run that skipped it says so.

---

## 5. The report line

One line in the Step 6 report, every run, in this form:

```
MAINTAINABILITY: M1 <n> / M2 <n> / M3 <n> / M4 <n> gaps (tools/maintainability.py),
  hubs + comment intent judged by hand on <k> files: <the paths>
```

A line with the four counts and no hand-judged paths is the vacuous half of this check: the tool
cannot see the two rules that matter most. `0 gaps` with no paths named means the tool ran and
nobody read anything.
