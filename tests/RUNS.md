# Fixture runs

| Date | Skill commit | Runtime | Tier | Hits | Near | Miss | False+ | Minutes | Note |
|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | no run recorded yet; first run establishes the baseline |
| 2026-09-15 | 5b5186d + the external-lessons edits (browser-walks.md, S2.1, S16.2, S19.1, S20.2, doctrine §8.1–8.2) uncommitted | Claude (subagent, cold) | Screen — `pre-launch audit, Screen tier` on fixture-service | 6 | 4 (S2 HIGH vs CRITICAL; S3, S22, S21-vacuous MEDIUM vs HIGH) | 0 | 0 | 10 | **First baseline.** All 10 planted sites found with path:line and a quoted line; both controls verified; commerce detection none; 4 extra true findings (finish() without a status predicate, untyped config → job stranded running, S19 no host, heartbeat partial write). Every near is a grade one level low on a money/safety path — the severity floor added to reporting.md the same day. 185k tokens. |
