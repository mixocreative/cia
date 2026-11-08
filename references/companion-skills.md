# Companion skills and tools — when cia hands a bounded job to another skill, and how the AI gets a tool it lacks

> Job of this file: tell the AI **which other skill or tool does a step better than cia**, what to hand over, what comes back and how cia grades it — and, when the skill or tool is not installed, **how to find, vet and install it** without changing anything the owner has not approved. cia keeps the verdict; a companion does a job.
>
> Skill names are as installed on the owner's machine on 2026-11-09. On any other machine, check availability first (§3) and fall back (§4) when a companion is missing.

---

## 1. The rule

- **A companion takes a bounded job, never the audit.** cia stays the auditor or the builder. The companion's output is evidence or a proposal, graded under cia's own rules (`evidence.md` §E1, `reporting.md` §9).
- **Announce every handoff** in one line in the conversation ("handing the screen polish of SRF-04 to `impeccable`") and in the report's COMPANIONS line (§5).
- **Another auditor's doctrine is still suggested, never imported.** `ecommerce-cia` is named to the user (`SKILL.md` §0.4); it is not loaded by this table.
- **Hand off when the companion is better at the step, not to spread work.** Each handoff costs a brief and a verification (`agent-deployment.md` §4–§5). If cia's own file answers the question, use it.

---

## 2. The handoff table

| When | Companion | Hand over | Comes back | cia grades it as |
|---|---|---|---|---|
| A screen the surface map or the walkthrough found weak needs design work: hierarchy, empty-state copy, an unclear control | `impeccable`; on a Mixo app, `mixo-app-style` first (its tokens are fixed, never re-derived) | the `SRF-` ids, the finding, the screenshot | a design change or a critique | a proposal; after it lands, the surface-map cells and walkthrough rows are re-checked |
| The surface map or the walkthrough needs the real screens of a running app | `stitch` (captures a running app into screens) | the app URL and the screen list | screen captures | `●(read)` evidence; **ask the owner before binding a Stitch project or uploading screens** (owner rule) |
| Accessibility of the critical journeys | `design:accessibility-review` | the critical journeys' screens | WCAG findings | findings, graded under `reporting.md` §9 |
| Wording on a step fails walkthrough W1 or W4 | `design:ux-copy` | the step, the control, the failed question | replacement copy | a proposal; the walkthrough row is re-asked |
| A step can harm a person (clinical or medical-device use), or a use error has a physical cost | `meddev-iec-62366-usability`, `meddev-iso-14971`, `meddev-state-machines`, `meddev-traceability` | the critical journeys and their use-error rows | hazards, risk controls, trace IDs | `RISK-` rows (`build-orchestration.md` §7); controls get guard tests |
| Ranking the failure modes of critical journeys before a build | `fmea-analysis` | the grid cells marked `✕` or `U` | severity × occurrence × detection | an order of work; it never replaces cia's severity |
| A defect keeps coming back, or nobody agrees on its cause | `rcca-master` (it chooses `five-whys-analysis`, `fishbone-diagram`, `fault-tree-analysis`) | the finding with its evidence | a root cause and a corrective action | the corrective action becomes an obligation row (`evidence.md` §E3) |
| Choosing between two designs, libraries or architectures | `trade-study-analysis` or `kepner-tregoe-analysis` | the options and the criteria | a scored decision | an ADR (`design-tools.md` §5) |
| Drafting a spec, or a cold review of one | EGM `/egm:egm-draft`, `/egm:egm-review` | the journey, spec or test plan | a deficiency list | `test-tools.md` §2 |
| Bulk mechanical reading, or a local model | `token-economy-delegation` | the bounded task | the list | `agent-deployment.md` §5 |
| A strict maintainability review of a diff | `pstack:thermo-nuclear-code-quality-review` | the diff | findings | the maintainability rules in `build-orchestration.md` §4 |
| A security review of the pending changes | `security-review` | the branch | findings | graded under `reporting.md` §9 |
| A second opinion from another model family | `gemini` (the owner's bridge) | one finding or one design question | an answer | a lead, never a verdict |
| Creating or fixing one of the owner's own skills | `skills-hub` | the skill name | the scaffold or fix | never hand-make a skill folder |

---

## 3. When a skill or tool is missing — find, vet, install

Run the steps in order and stop at the first that resolves it.

1. **Probe.** Is it there? The session's skill list, the tool's `--help`, the plugin list, the project's lockfile.
2. **Find.** Use the runtime's own discovery: Claude Code's skill and plugin search where the session has it, the `find-skills` skill where installed. For a GitHub tool, find the **official** repository or package (the project's own org, not a fork or a mirror).
3. **Vet before installing.**
   - official source; license compatible with the project;
   - maintained (recent commits or releases);
   - read the install command and what it writes: hooks, MCP config, `CLAUDE.md` / `AGENTS.md`, global settings, other repositories;
   - never pipe an unread remote script into a shell.
4. **Install by scope** — the self-service ladder of `SKILL.md` §0.8:
   - a dependency the project's lockfile already pins → rung 2: install it;
   - a user-scope CLI (`pipx`, a user `npm` prefix, a portable binary) → rung 3: install it and record what and where;
   - a plugin or marketplace install, an MCP server registration, hooks, global settings, or anything that writes into the user's configuration or another repository → **ask the owner first** (rung 5), with the exact command, what it writes and why the run needs it. The owner runs it or approves it.
5. **Probe again** and record the version in the COMPANIONS line and the handoff. If it still does not work, use the fallback in §4 and say so.
6. **The owner's own skills** come from `skills-hub` (`pwsh -File S:\ai\skills\skills-hub\hub.ps1 new|adopt|publish|doctor`), never from a folder made by hand or copied between agents.

---

## 4. Known tools — where the install comes from, and the fallback

Install commands come from each tool's own documentation; check them against the version being installed.

| Tool | What cia uses it for | Install source | Scope | Fallback when missing |
|---|---|---|---|---|
| graphify | architectural context, blast radius | its README | user-scope CLI | grep |
| CodeGraphContext (`cgc`) | code relationships | its README (a Python package); `cgc mcp setup` edits client config | user-scope; config needs the owner | graphify `explain` / `path` |
| EGM | cold-read reviews, drift reports | `claude plugin marketplace add google/elephant-goldfish-model && claude plugin install egm@egm` (its README) | plugin: owner approves | a fresh subagent with the same brief, recorded as such |
| dependency-cruiser | JS/TS dependency rules | `npm i -D dependency-cruiser` | project dev dependency | `tools/design_check.py deps` |
| import-linter | Python dependency rules | `pip install import-linter` into the project's dev dependencies | project dev dependency | `tools/design_check.py deps` |
| Playwright | browser walks, transition walks | `npx playwright install --with-deps chromium` (`SKILL.md` §0.8 rung 2) | project | a headless or CLI walk |
| meddev-agent-skills | medical-device usability and risk rules | the `AminAlam/meddev-agent-skills` plugin | plugin: owner approves | the use-error row in `journey-map.md` §2 |

---

## 5. Report line

```
COMPANIONS — handoffs: <skill: why, result graded as>; installs: <tool version, scope, who approved>; missing: <tool, fallback used>; none: n/a.
```

---

**Reading receipt: _a companion takes a job, never the verdict_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
