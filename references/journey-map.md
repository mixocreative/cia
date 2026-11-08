# Journey map — the workflows a person performs, every branch of them, and where each one ends

> Job of this file: enumerate the **workflows** (multi-step, multi-surface, over time) that matter, branch every step into the outcomes it can produce, and prove each branch ends in a state the person can see and account for. The surface matrix (`surface-map.md`) says what can be invoked; this file says in what order, under what conditions, and what happens when it goes wrong halfway.
>
> Adapted from `meddev-iec-62366-usability` (critical tasks with trace IDs, formative/summative evidence) and `ddunnock/specification-refiner` SEAMS (Sequence, Error, Recovery, Stakeholder categories). The branch grid and the arrival perturbations are this skill's own (S23).

---

## 1. Why the unhappy path gets missed

The author maps the path they walked. Everything else is filed under "error handling", which has no owner, no scenario and no test. The failures cluster in six places:

1. **The wizard that trusts its own order.** Step 3 can be reached without step 2 (deep link, back then forward, refresh). It then reads a value step 2 would have written and gets nothing.
2. **The interruption.** The person closes the tab after the charge but before the confirmation. The state is half-written and nothing resumes it.
3. **The second person.** Two people edit the same record; the first save wins silently, or the second person's form submits stale values.
4. **The changed world.** The item was deleted, the price changed, the role was revoked, the session expired — between step 1 and step 4.
5. **The asynchronous outcome.** The UI says "submitted" but the real result arrives later (a job, a webhook, an email). Nothing tells the person when it lands, or that it failed.
6. **The copy that lies.** A label says "Saved" when the handler has only queued the write; "Done" when the job is still running. The person acts on the label.

---

## 2. Critical journeys first

Not every workflow needs this rigour. The critical set is: any journey whose failure would **change the system's primary quantity** (`SKILL.md` §0 — the state the system exists to get right), **cannot be undone**, or **leaves a person unable to tell what happened**. Write the list before grading anything.

Each journey gets one row. Use a stable ID (`JRN-###`) and cite it from tests and walks, so the trace runs both ways:

| Field | Content |
|---|---|
| `JRN-id` | stable ID, e.g. `JRN-007` |
| Actor(s) | each role that can start it, and the one that finishes it when different |
| Goal | one sentence, in the person's words, that can be false |
| Entry surfaces | the `S-id`s from `surface-map.md` that start it |
| Preconditions | what must be true before step 1, and what the UI assumes about it |
| Steps | numbered; each step names the capability it invokes (`C-id`) |
| Exits | every terminal state, each marked **done / abandoned / failed / needs-human** |
| Primary quantity touched | which stored state changes, and where it is read back |
| Owner decision needed? | yes if an exit has no defined behaviour yet |
| Use errors | for each step marked critical: the plausible wrong action a first-time user takes (wrong object, wrong order, premature confirm, skipped undo), and the control that prevents or reverses it (path:line) — or `NONE`, which is a finding under T4 |

A critical step with no use-error row has been judged safe by its author, which is the one judge usability engineering excludes.

A journey with no `exit = needs-human` is one where something can get stuck without anyone being told. Check for that first.

---

## 3. Branch every step

For each step, enumerate the outcomes it can produce. Six come from the request itself; the arrival perturbations of S23 (duplicate, late, out-of-order, never, abandoned, back-button, refresh, second tab) come from how people and networks behave.

| Outcome | Meaning | Must end in |
|---|---|---|
| **Success** | the step's effect happened | the next step, or a terminal exit, visibly |
| **Validation rejection** | the input is wrong; nothing changed | the person sees which field and why, and can correct it in place |
| **Authority refusal** | the actor may not do this | a message that names the refusal and the way forward; not an empty screen |
| **Transient failure** | the dependency is down or slow | a retry the person can trigger, or a stated "not yet"; the state is unchanged |
| **Unknown result** | the request may or may not have taken effect (timeout after send) | a read-back that decides which, or a visible "check status" — never a silent resend |
| **Conflict / stale** | the record changed since the person loaded it | the person sees the current state and chooses; the older write does not overwrite silently |

The outcome table is the same authority table S22.4 requires. A step whose capability has an error class the table does not name has an UNKNOWN outcome, and the report says so.

---

## 4. The journey grid

One grid per critical journey. Columns are the branch kinds that matter; rows are the steps. Each cell holds a verdict and a site.

| Step | Happy | Reject | Refuse | Fail | Unknown | Conflict | Duplicate | Resume (refresh/back) |
|---|---|---|---|---|---|---|---|---|
| 1. … | ● path:line | ● | ● | ✕ | U | ○ n/a | ● | ✕ |

Verdicts:

- `●` handled and the outcome is visible — cite the message or state the person sees (path:line);
- `✕` handled wrongly or not at all — say which of the §5 traps;
- `U` unknown — the branch is not defined in code or in the spec; it becomes an open owner decision;
- `○ n/a` the branch cannot occur for this step — say why, with the guard that makes it impossible (path:line).

A blank cell is an unswept cell and is counted as such.

---

## 5. The traps — checks that run across the grid

**T1 — Stuck state.** Some state has no exit a person can take: spinner with no timeout, disabled button with no reason shown, "processing" with no link to status. Check: every non-terminal state has an exit the UI renders (S16).

**T2 — Confirmation that lies.** The label or toast says a thing the handler did not do ("saved", "sent", "paid", "deleted") — compare the copy with the write, line by line. Queued is not saved; requested is not sent.

**T3 — Reachable out of order.** Step *n* can be reached, or its action submitted, without the state step *n−1* produces. Check by opening step *n* directly, from a fresh session (`surface-map.md` SC6).

**T4 — Irreversible without a gate.** A step that changes the primary quantity or cannot be undone has no confirmation that describes the action, no undo, and no way to see it afterwards.

**T5 — Progress lost.** Refresh, back or a closed tab discards entered state the person cannot cheaply re-enter, with no warning.

**T6 — Two editors, one record.** Two actors can save over each other with no conflict signal, or the second save succeeds against values the first one changed.

**T7 — Async result nobody reports.** The journey ends at "submitted" but its real outcome arrives later through a job, webhook or email, and no surface shows it. This is S16 in the journey's own words: every flow must end somewhere a person can account for.

**T8 — The mode error.** A surface offers an action whose preconditions are not met in the current mode (edit mode off, offline, read-only, draft vs published) and explains nothing. S22.6.

Each trap that fires is a finding, graded under `reporting.md` §9, with the grid cell it sits in.

### 5a. The cold-reader walkthrough — can a person find the way

For every step of a critical journey, a reader with no context (an EGM Goldfish or a fresh subagent, `test-tools.md` §2) answers four questions from the screen alone (a cognitive walkthrough):

- **W1** — would I know to do this now?
- **W2** — can I see the control?
- **W3** — would I pick this one over its neighbours?
- **W4** — after acting, do I know it worked and what comes next?

A "no" is a finding on that grid cell, graded MEDIUM — HIGH when the step is critical and the wrong neighbour is irreversible. Record it as `●(read)`: a walkthrough judges wording and layout, never behaviour. Run it at Walk tier for every critical journey and at Screen tier for the primary one; real screens come from the running app (`companion-skills.md`, `stitch`).

---

## 6. Keeping the possibility space finite

Journeys explode combinatorially: steps × outcomes × actors × states × configuration. Mapping "all possibilities" by feel covers the cases the author already imagined. Reduce it mechanically, and write the reduction down so a reader can see what was left out and why:

1. **Equivalence classes per step.** Group the outcomes of one step into classes that the next step treats identically. Test one representative per class, plus the boundary values (S18 enumeration against the authority document).
2. **Decision table for the rule.** When a step's outcome depends on several inputs (role × state × amount), write the table and cover every row. A table with an empty row is a finding (`evidence.md` §E5 bounded negatives).
3. **All-pairs for configuration.** Configuration switches that a journey reads (feature flags, locales, plan tiers) are covered pairwise, not exhaustively; a pair that fails is a finding even when each switch alone passes.
4. **Full grid only for critical journeys.** Non-critical journeys get the happy path, the refusal, and the unknown-result branch. The critical ones get the whole grid.

State the reduction in the report as a line: `reduced by classes (k), decision rows (r), pairwise configs (p); full grid for critical journeys J`.

---

## 7. Sign-off — when a journey counts as covered

A journey is covered when every cell in its grid has a verdict, every trap in §5 is checked against it, and each `●` cell is backed by an artefact that could fail:

- an automated test that fails when the branch is broken (guard test, `test-tools.md` §4);
- or a walk using the state-delta ladder (`browser-walks.md` §12) that observes the outcome on screen;
- or, for a judgement about findability and wording, a cold reader's review (`test-tools.md` §2, the EGM Goldfish pass).

A `●` backed only by reading the code is recorded as `●(read)`, not `●`. Reading never produces a PASS for a runtime behaviour (`evidence.md` §E1).

---

## 8. Report line

```
JOURNEY — J critical journeys (of J' found); steps T; grid cells G: ● P (read R), ✕ F, U unknown, ○ n/a, unswept X;
          traps checked 8 of 8, fired F_t; exits without owner decision O; reduction: classes k, decision rows r, pairs p.
          sites: <JRN-id path:line per finding>; one quoted copy line with the write it describes.
```

---

## 9. Where this sits in the protocol

Journeys are built from the surface matrix, so run `surface-map.md` first. The journeys are the input to the browser walks (`browser-walks.md`) and to the four-corner walk (S15). For a build, the journey list is written before any code (`build-orchestration.md` §2).

---

**Reading receipt: _the author walked one path and called it the journey_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
