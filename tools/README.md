# tools/ — map

Every file here, grouped by who runs it. Run each from the skill root; each answers `--help`.
`check_structure.py` fails when a file in this folder is missing from this map.

## An audit or a build runs these

| File | Job |
|---|---|
| `route.py` | SKILL §0.5, every run. Step 0 scan: facts with path:line that route the run to references, graphs and companions; leads, never verdicts |
| `route_tree.py` | route.py's tree walk under the skip, secret and symlink rules |
| `route_companions.py` | route.py's COMPANIONS line: which companion skills and CLIs are installed |
| `route_render.py` | route.py's text output, including which graph answers which question |
| `maintainability.py` | SKILL §0.6 Step 2, every run. M1-M4 of `references/maintainability.md` on any git repo: folder maps, size debt, the module's job line, living-doc links. Says in its own output which two rules it cannot see |
| `sweep_leads.py` | SKILL §0.5, after route.py: the S13 and S21 sites a script can list, each needing a finding or a reason |
| `inventory.py` | optional, no SKILL step calls it (tried as a Codex step and taken out): every function, test, config key and write, for item-by-item answers |
| `design_check.py` | `references/design-tools.md`: dependency rules, ADR hygiene, state-transition tables; stdlib only |
| `audit_report.py` | SKILL Step 6: checks an audit report's shape: blocks, receipts, sweep lines, Step 6 lines |
| `stop_check.py` | the plugin's Stop hook (`hooks/hooks.json`): a session that wrote this skill's audit report cannot finish while the checker fails; blocks once, never loops |
| `build_report.py` | SKILL §0.10a: prints the build report form and checks a build report's shape |

## The maintainer runs these (push gate, CI)

| File | Job |
|---|---|
| `score.py` | the skill's own score from `tests/RUNS.md`, and the push gate |
| `untested.py` | refuses doctrine (`SKILL.md`, `references/`) with no scored run |
| `due.py` | which comparison arms and EGM reviews are due, with the command for each |
| `check_structure.py` | the skill's files agree: nothing loose, S1-S24 once, size debt named, versions, this map, no line the Read tool cuts |
| `check_key_lines.py` | the answer keys still point at the fixture lines they cite |
| `receipts.py` | every reference has one unique reading receipt |
| `zh_check.py` | Chinese text uses Taiwanese, not mainland, usage |
| `sweep-diff.py` | compares the doctrine shared with `ecommerce-cia` |
| `pre-push` | the git hook that runs the gate |
| `install-hooks.sh` | installs `pre-push` into this clone |
