# Surface map — how a function fails to reach a screen, and how the audit finds it

> Job of this file: build the matrix between **what the system can do** (capabilities) and **where a person or an outside party can ask for it** (surfaces), then check every cell for the five ways that mapping breaks. Cross-cutting companion to the sweeps: S5 (dead control), S13 (orphan capability), S11 (boundary drift), S16 (terminal states), S22 (surface completeness). Journeys — the multi-step workflows that run across surfaces — are in `journey-map.md`.
>
> Adapted from the same idea in `meddev-iec-62366-usability` (critical tasks traced to UI elements) and `ddunnock/specification-refiner` SEAMS (Structure ↔ Execution ↔ Mismatch: requirement-to-design coverage). The matrix and the miss taxonomy below are this skill's own.

---

## 1. Why a green suite does not see this

Each test layer checks one side of the mapping and trusts the other:

| Layer | What it proves | What it trusts without checking |
|---|---|---|
| Unit tests on the service | the function does what its author meant | that any screen calls it, with the right fields, as the right role |
| Component tests | a control renders and fires *a* handler | that the handler is the right capability, and that the fixture states are the states the real capability returns |
| End-to-end happy path | one walk the author scripted reaches the outcome | that the other surfaces, roles and states work |

The gap lives in the **mapping** — which control invokes which capability, under which role, in which state. No layer owns the mapping, so no layer tests it. The matrix makes it an object someone can count.

---

## 2. The five ways the mapping breaks

Name the miss by its mechanism. A finding that says "the cancel button is missing" has not said which of these it is, and the fix differs.

| # | Miss | Mechanism | Sweep | Typical sign |
|---|---|---|---|---|
| M1 | **Orphan capability** | the function exists and is tested; no surface invokes it, and no scheduled job or event consumer owns it either | S13 | a `cancel_order()` / `export_csv()` nobody calls; an admin path only reachable from a shell |
| M2 | **Dead or hollow control** | the control renders; its handler is missing, a no-op, a TODO, points at a removed route, or swallows the response | S5, S22.9 | a `data-action` with no handler; `onClick={() => {}}`; a menu item whose route 404s |
| M3 | **Silent field drift** | the control submits a payload the capability reads under a different name or ignores; the request succeeds and does a different thing | S11 | a "priority" dropdown posted as `prio`, read as `priority` with a default; the UI shows the value it sent, the record holds the default |
| M4 | **State blindness** | the capability returns states the screen has no branch for — pending, partial, rejected, conflict, stale, forbidden, timed out, retried — so the screen shows success, or a spinner that never stops | S16, S22 | a spinner after a 409; success text after a job that is still `queued`; a 403 rendered as an empty list |
| M5 | **Audience mismatch** | the surface is visible to a role the capability refuses, or hidden from a role it allows; the refusal lands with no message | S22 (audience axis), S17 | a button shown to viewers that 403s with an unhandled error; the editor role cannot see the button the API allows it |

Two more appear only when the matrix is built across surfaces:

| # | Miss | Mechanism |
|---|---|---|
| M6 | **Two-surface drift** | the same capability from two surfaces (row action, detail page, bulk action, API, CLI) applies different validation, confirmation or outcome text |
| M7 | **Reachability gap** | the surface only renders from in-app navigation state: a deep link, a refresh, the back button, a second tab, or a stale tab whose data has moved on shows a different screen or nothing |

---

## 3. The method — three inventories, then the matrix

Build the three lists first, from the code, before judging any cell. Every row cites a `path:line` a reader can open.

### 3.1 Capability inventory (C-list)

Every function, endpoint, job handler, message consumer or CLI verb that **changes state or returns something a person must see**.

- Sources: route/controller tables, public methods of service classes, job or queue registries, message handlers, CLI argument parsers (`argparse`, `click`, `commander`, `cobra`, `clap`), scheduled task tables.
- Per row record: `C-id`, name, `path:line`, **actors allowed** (the authorization check, `path:line`), **return states Σ** — enumerate from the return type and the error table, not from memory (S22.4: the authority's error table is the outcome column).

### 3.2 Surface inventory (S-list)

Every place an actor can invoke a capability: buttons, menu items, row and bulk actions, context menus, keyboard shortcuts, drag-and-drop, deep links, API routes, CLI flags, webhooks, emails and notifications with an action link, scheduled triggers.

- Sources (grep, then read the hits):
  - UI event bindings: `onClick`, `@click`, `on:click`, `(click)`, `onSubmit`, `data-action`, `hx-post`, `addEventListener('click'`.
  - Menu and action definitions: menu config arrays, toolbar registries, keymap files.
  - Route registration: `router.`, `app.get(`, `app.post(`, `@app.route`, `Route::`, `urls.py` `path(`.
  - Notification and email templates: `href=`, `url_for(`, `reverse(` inside mail/notification templates.
- Per row record: `S-id`, location `path:line`, **invokes C-id** (or `NONE`), **audience** (who sees it — the render condition, `path:line`), **preconditions shown** (what the surface disables or hides and why).

### 3.3 Journey link (J-list)

Each S belongs to one or more journeys in `journey-map.md`. A surface in no journey is either a leftover or a journey nobody wrote down; both are findings.

### 3.4 The matrix

Rows = capabilities. Columns = surfaces (plus `API` and `CLI` columns when they exist). Each cell is one of:

- `●` a surface reaches this capability, and the audience, preconditions and states were checked;
- `○` no surface reaches it, with a declared reason (system-only, scheduled, internal) and a named owner;
- `✕` a surface reaches it but the check failed — say which (M2, M3, M5…).

Blank cells are not allowed. A blank is an unswept cell, and the report counts it as such.

---

## 4. The checks, and what each one catches

Run these over the matrix. Every failed check is a finding, graded under `reporting.md` §9.

**SC1 — Orphan.** A C-row with no `●` and no declared `○` owner → M1. Allowed only when the owner is a named scheduled job or event consumer, cited by path.

**SC2 — Dead control.** An S-row with `invokes = NONE`, or with a C-id that no longer exists in the C-list → M2. Grep the handler for the `data-action` value (S22.9): a rendered button is not a wired control until its handler is read.

**SC3 — Audience gap.** For every `●` cell: the actors that can see S must be a subset of the actors C allows. Visible-but-refused → M5. Also the reverse: allowed-but-hidden is a finding when the role has no other way in.

**SC4 — State coverage.** For every `●` cell, each state σ in Σ(C) must have a rendering branch on S: loading, success, each named error, partial, pending/async, conflict, forbidden, timeout, and "unknown result" (the request may have run). A missing branch → M4. Check the branch renders, not only that it exists: use the state-delta ladder (`browser-walks.md` §12) or a fixture that returns the state. A fixture the author wrote proves the author's assumption (S24).

**SC5 — Round trip.** For every input control on S: the name it submits matches the parameter C reads, the default when absent matches the default the user sees, and no field is dropped without a log line. Trace it with the four-corner walk (S15): control value → request body → handler → stored row → read-back to the same control. → M3.

**SC6 — Reachability.** For every S: open it from a fresh session by its deep link, after a refresh, from the back button, and from a tab opened before the state changed. A surface that needs in-app state it cannot recover → M7.

**SC7 — Cross-surface consistency.** Two `●` cells on the same C row: validation rule, confirmation text and outcome text must match (or the difference must be declared). → M6.

**SC8 — Irreversibility.** A `●` on a C that changes the primary quantity (`SKILL.md` §0 — the state the system exists to get right) must have a confirmation or an undo, and the confirmation must describe the same action the handler performs (not "saved" when the handler only queued it).

---

## 5. Mechanical hunts, cheapest first

Use the graph before reading files, routed by `code-graph-tools.md` §2: CodeGraphContext for a capability's callers once it is in place, otherwise `graphify explain "<capability name>"`. The callers and their files narrow the grep. Then:

1. `grep -rn "data-action\|onClick\|@click\|on:click" <ui-dir>` → the S-list raw hits.
2. For each hit with a handler name, `grep -rn "<handler>"` → the C it reaches; a hit with no definition is M2 candidate.
3. `grep -rn "<capability name>"` across the service and job dirs → callers; zero callers outside its own file and tests → M1 candidate.
4. For each C, grep its error classes (`class .*Error`, `raise`, `throw new`, error-code enums) → Σ(C).
5. For each S, grep for the branch on each σ in its component (`status ===`, `case '`, `if (error`, `.catch(`) → SC4 check.

Each hunt's counts go in the report line with the sites. A count without sites is not evidence (S8 applied to the audit).

---

## 6. Report line

```
SURFACE — C capabilities (O orphan, declared-owned D); S surfaces (N dead, A audience-gap); cells: ● P, ○ Q, ✕ F, unswept U;
          state branches rendered R of Σ-total; round trips checked T (dropped fields X); reachability checked K of S.
          sites: <path:line per finding>; one quoted line from the handler of one ● cell, verbatim.
```

An `unswept U` above zero is printed, not hidden. Zero unswept cells is the only way the line says the matrix is complete.

---

## 7. Relation to the other sweeps

| Need | Read |
|---|---|
| The rule that a control must have a handler | `sweeps/01-state-and-boundaries.md` (S5) |
| The rule that a capability must have a caller | `sweeps/02-tests-cascades-scope.md` (S13) |
| The rule that every flow ends where a person can see it | `sweeps/03-flows-and-terminal-states.md` (S16) |
| The step × outcome × audience grid and the authority error table | `sweeps/05-surface-completeness.md` (S22) |
| Per-route rendering checks | `browser-walks.md` §10 |
| Multi-step workflows across surfaces | `journey-map.md` |

## 8. Known limits

- The matrix is only as complete as the inventories. A capability registered dynamically (plugin loaders, reflection, generated routes) will be missed by grep; say so and list the registration mechanism as UNKNOWN (`evidence.md` §E4), do not call the matrix complete.
- A `●` cell proves a path exists in the code. It does not prove a person can find it. Findability is a usability question: the cold-reader walkthrough in `journey-map.md` §5a decides it.

---

**Reading receipt: _every blank cell is a cell nobody swept_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
