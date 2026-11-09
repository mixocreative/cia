# fixture-editor architecture

## A1 — Saves are atomic

`store.saveDoc` writes the new version to a temporary file next to the document and renames it
over the document, so a crash or a full disk mid-save leaves the previous version intact. A user
never opens a half-written document.

## A2 — A stale save is refused and shown

Every save carries the version the editor loaded. A save based on an older version than the one on
disk is refused with status `conflict`, and the title bar shows a **Conflict** badge with
**Reload** and **Keep mine** actions. Two windows on one document therefore never silently
overwrite each other.

## A3 — Backups

The last `backupCount` versions of each document are kept beside it as `<id>.json.bak1` …
`<id>.json.bakN`, newest first. **Restore** in the File menu (`backup.restoreBackup`) brings one
back.

## A4 — Thumbnails degrade, they do not fail

A thumbnail is a convenience in the document list. Nothing acts on it and no save depends on it,
so `thumbs.thumbnail` catches its own rendering errors and shows "preview unavailable" — a visible
degradation, never a blank tile that looks like an empty document. This is the one place in the
editor where a fail-open posture is the intended choice, and it is the choice because the path is
display-only.

## A5 — The recent list is a window, not an index

`store.listDocs` returns the newest `recentLimit` documents for the start screen and offers no
paging: the start screen is for picking up recent work. Any document is reachable by id with
`node src/cli.js open <id>`.
