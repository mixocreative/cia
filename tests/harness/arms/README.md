# Comparison arms

What `cold_run.py --arm` swaps in for the cia skill, so the same audit task can be scored without it.
Rows go to `tests/ARMS.md`; `tools/due.py` says when a new comparison is due.

| Arm | What the run gets instead of cia |
|---|---|
| `none` | One line: no skill is provided, audit with your own judgement. |
| `ponytail` | The body of `ponytail-audit/SKILL.md`, pasted into the prompt. |

## ponytail-audit

- **Source:** [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), `skills/ponytail-audit/SKILL.md`
  at commit `96608e078b2d5ea607c5c3b8b5a54d1c1fba6846` (2026-11-09). MIT; the licence is copied beside it.
- **Unchanged.** To move to a newer version, fetch the file at a new commit, update `PONYTAIL_COMMIT`
  in `cold_run.py`, and start new rows in `tests/ARMS.md`. Never compare across two pins as one arm.
- **What is left out, on purpose.** The ponytail plugin is not installed and none of its hooks run:
  its activation hook would put ponytail's base persona into every session on this machine, the
  cia runs included, and nothing in `RUNS.md` would show it. Ponytail's own benchmark notes that
  pasting a SKILL.md approximates the installed plugin; that limit applies to this arm.

## How an arm is kept away from cia

- `Read(./**)` instead of `Read`: the run can read its fixture copy and nothing else (checked
  2026-11-09: a headless run was denied `S:\ai\skills\cia\SKILL.md`).
- `--disable-slash-commands` and no `Skill` tool, so the installed cia skill cannot load.
- The report header carries `cia-traces`: cia-only vocabulary found in the report. Anything but
  `none` means the run reached cia some other way (python can read files), and the row is void.
