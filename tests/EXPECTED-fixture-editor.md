# fixture-editor — answer key

**Eleven** planted defects, **one tracked extra** the fixture acquired by accident (E12), and **seven** verified controls in a Node notes editor whose primary
quantity is **the saved document on disk**. A Screen-tier `/cia` run on this directory must report
every row below with a sweep, a `path:line` inside the cited range, and a grade no lower than
shown. Scored like `EXPECTED-fixture-service.md`: hit 1, near (late, a grade low, or unanchored)
0.5, miss -1, a control filed as a defect -1.

**Why a second fixture (2026-11-09).** Every audit row before this date was scored on
`fixture-service`, a Python job queue, so a doctrine change could fit that one project's shapes
and pass. This fixture shares no code, no language and no primary quantity with it, and two of its
classes are ones the step-0 scans cannot list (a shared config object mutated by a test, and
overlapping autosaves), so a run cannot score here by dispositioning the scan.

Run the suite first (`node --test`): 8 tests, all green. Every defect below sits under that green.

## Planted defects

| # | Sweep | Site | Defect | Invariant broken | Min grade |
|---|---|---|---|---|---|
| E1 | **S12** partial failure (or build-standard §1.1 atomic) | `src/store.js:29-32`; `docs/ARCHITECTURE.md` A1 | `saveDoc` writes the document **in place** with `fs.writeFile`; a crash or a full disk between the truncate and the last byte leaves a half-written JSON file. A1 promises temp-file-and-rename. | A save of the primary quantity lands whole or not at all | HIGH |
| E2 | **S2** check-then-act | `src/store.js:24-31` | The version check (`await loadDoc`, compare) and the write (`await fs.writeFile`) are separated by awaits, so two saves with the same `baseVersion` both pass the check and the second silently overwrites the first. A2 promises the stale one is refused. | The precondition and the write are one decision | HIGH |
| E3 | **S3** fail-open on the primary path | `src/store.js:12-19` | `loadDoc` catches **every** error (a corrupt or half-written file, a permission error, not only a missing file), logs at `console.debug`, and returns an empty document at version 0. The editor shows a blank document, the next save's version check passes (`0 === 0`), and the real file is overwritten with the blank one. With E1 a crash mid-save becomes permanent loss. | Only "does not exist yet" may become a new document; any other read failure is loud | HIGH |
| E4 | **S5** dead control | `config.json:4` `backupCount`; `src/config.js:10` | Nothing writes backups and nothing reads `backupCount` (grep → config and defaults only). A3 promises the last N versions are kept. | Every control has a consumer | MEDIUM |
| E5 | **S13** orphan capability | `src/backup.js:7-10`; `docs/ARCHITECTURE.md` A3; `README.md` | `restoreBackup` has no caller and no menu or command reaches it; the README tells the user to restore from the File menu, and no backup file is ever written for it to read. Designed, documented, unbuilt. | A capability a document promises exists or has a gap-register row | MEDIUM |
| E6 | **S20** blind instrument (or S3 on the badge) | `src/autosave.js:27-29` | A failed autosave is caught, logged at `console.debug`, and the status is **put back to what it was** — so the badge keeps saying "Saved <old time>" while every save fails. The person's one safety signal reports success it no longer has. | A detector reports failure; a status never outlives its evidence | HIGH |
| E7 | **S22** unrendered state | `src/render.js:8-17` | `BADGES` has no `conflict` renderer and `badge()` returns `''` for an unknown state, so a refused save (E2's protection, when it fires) shows **nothing**. A2 promises a Conflict badge with Reload / Keep mine; neither action exists. | Every reachable state has a surface | HIGH |
| E8 | **S23** interleaving (or S2) | `src/autosave.js:34-36` | `setInterval(saveAll, …)` starts a new `saveAll` whether or not the previous one finished, with no in-flight guard; two passes overlap on one document, both carry the same `baseVersion`, and the slower write lands last (older content wins, or E2 fires on its own session). | One save per document in flight; arrivals are serialised | MEDIUM |
| E9 | **S11** boundary / S11.1 byte splitting | `src/titles.js:7` | `fileNameFor` truncates the UTF-8 **bytes** to `maxTitleBytes` and decodes, so a title with a multi-byte character at the cut ends in `U+FFFD`, and two titles that differ only after the cut export to the same file name. | Text is cut on characters, not bytes | MEDIUM |
| E10 | **S21** runner contamination | `tests/editor.test.js:56-59` | The test sets `config.maxTitleBytes = 8` on the **shared** config object and never restores it (the `afterEach` restores only `dataDir`), so every later test in the process runs with an 8-byte title limit; `export writes the document as markdown` passes only because it computes its expectation through the same mutated function. | A test leaves shared state as it found it | MEDIUM |
| E11 | **S21** vacuous pass | `tests/editor.test.js:49-54` | `a fresh session has no conflicts` asserts `conflicts()` is empty, and no test anywhere makes it non-empty, so it would pass if `conflicts()` always returned `[]`. Beside it, the listing tests (`:38-47`) are the paired shape done right. | A test asserting emptiness needs a sibling proving non-emptiness | MEDIUM |

Also expected, not separately scored: **S14** — the run states its scope as this directory; **S19** — `dataDir` resolves against the project root (`src/config.js:19`), so no host requirement is in question; `titleBar` (`src/render.js:20`) has no caller in the tree (there is no window host here), which a run may file as S13 or name as a boundary; one corrupt document in `listDocs` (`src/store.js:46`) fails the whole start screen, a true extra.

### E12 — tracked, not scored (re-decided 2026-11-09)

| E12 (tracked) | **S1 / S23** stale entry under an in-flight save (not planted) | `src/autosave.js:10-13`, `:20-22` | `edit()` replaces the map entry while `saveAll` holds the old one; the save then advances the **old** entry's `baseVersion`, so the new entry still carries the version before the save and every later tick is refused as a conflict with the session's own save. Typed text never reaches disk, and E7 means nobody is told. | One owner of a document's base version; a save advances the entry the editor is using | HIGH |

E12 is **not one of the eleven scored rows**, and a run that misses it is not charged a miss. It was added to this key after the baseline, because the first two runs found it; seven runs later it had been found in five (EA, EB, EC, EF, and as ED-010) and missed in two (ED, EE), one of them a run that read every reference. A row the zero-tolerance miss rule guards must be one a sound run finds every time, or the gate turns into a coin flip on a sound commit. E12 is the measure of depth beyond the planted list: the RUNS note records whether each run found it, and README reports the rate. Re-decided after run EE missed it, which is the moment a reader should be most suspicious of; the rate, not that run, is the reason, and it is printed above.

### A note on E12's provenance

E12 was **not planted**. `edit()` was written to keep the base version of an open document, and it
does, on a new object, while `saveAll` advances the old one. Both cold runs on the first day (EA,
EB) found it with a probe, before anyone had read it as a defect. It is kept for the reason
fixture-service keeps its row 11: a defect a fresh run found that the author did not know was there
is the best evidence the fixture is not just the author's list.

## Verified controls (must appear under Verified Controls, not as findings)

| Control | Site | Looks like | Why it is correct |
|---|---|---|---|
| **Export is atomic** | `src/cli.js:8-15` | E1 — a file write | It writes `<target>.tmp` and renames it over the target: the correct twin of the save path. A run that files it has not read it; one that cites it as the shape `saveDoc` should copy has. |
| **Thumbnails degrade** | `src/thumbs.js:10-16`; ADR A4 | E3 — a catch that returns a default | Display-only, named by A4 with its reason, and visible ("preview unavailable", never a blank tile). Nothing acts on it. |
| **`listDocs` catches only ENOENT** | `src/store.js:38-43` | a swallowed error | A missing data directory is "no documents yet"; every other error is re-thrown. Filing it as a swallow means the auditor read `catch` and stopped. |
| **The recent list is a window** | `src/store.js:49`; ADR A5 | an unpaged list (S22.7) | A5 names the cap and where single documents live instead, and its premise holds: `node src/cli.js open <id>` (`src/cli.js:23-26`) reaches any document. Disagreeing with the cap is an owner question. |
| **`offline` has a renderer** | `src/render.js:11` | — | The counterpart of E7: four of five states render, which is what makes `conflict`'s absence a defect. |
| **`autosaveSeconds` has a consumer** | `config.json:3` → `src/autosave.js:35` | E4 — a dead control | Read by `start()`. A bare-identifier grep hits config, defaults and exactly one runtime reader. |
| **Config fails closed** | `src/config.js:15-21` | E3 — config loading | No catch: a missing or malformed `config.json` throws at start-up, which is the posture fixture-service's `load_config` lacks. Filing it as "no error handling" is a false positive. |

## Gate and trigger

- `route.py` reports page ≥ 1 and cli = 1 (`src/cli.js`); SURFACE and JOURNEY are therefore not `n/a`.
- `sweep_leads.py` lists `restoreBackup` and `titleBar` under S13 and nothing under S21: E10 and E11 must be found by reading.
- `cia` §0.3 commerce detection must report **none**.

<!-- site-pins (tools/check_key_lines.py) -->

## Site pins

Every file this key cites, with the sha256 it had when a person last read the ranges against it. A changed digest fails `tools/check_key_lines.py` — re-read, then re-pin.

- `config.json` ed89c45328d08a05ca4a44819c1811f2a079c967ada28f8ec8e47e87b9dbc228
- `src/autosave.js` e35d0bc2803666b54be3557d533cbb6a7b4c7c93030bcd1ab48251c76d7b2d73
- `src/backup.js` 4bc4d9b37aceb52c61af4ca5fd99b0aa2fbadd5928b49bc3ec29022eb0c10a8a
- `src/cli.js` 43d89643108109649d34f12ebf763b79ec577bb043c8ccc997c212d5f79c9f7c
- `src/config.js` 50257181a0bb75cbc0414f71c34499cb813c1cb5d3aa0bae01a5a55a90282063
- `src/render.js` f52618b432cf22baa343618c50c821a9684e74f875735b3bc8d358cc02e0d104
- `src/store.js` c6f1d650f52a30bea295b7d5009794c97fe8a5a12040cf7b2bae23d69145f38b
- `src/thumbs.js` e89cc2b510c98a25b374bf44fa4a7e6b3358f0e7b546f4ead05f5bfb0e11b4c0
- `src/titles.js` 222325077ee20bbedfac31a107fd35544daec5f9c76da90c57a7e3d6166b9a02
- `tests/editor.test.js` 0ad3e9eb8523939addd0ebe973c9bd36500c66afcf2196027c1f1e74de794cd0
