# fixture-editor — a planted-defect document editor for testing `cia`

A small Node service (Node 22, no dependencies) behind a desktop-style notes editor: it loads and
saves documents as JSON files, autosaves open documents on a timer, draws the save badge in the
title bar, and exports a document as Markdown. Its tests pass. It holds planted defects and
correct look-alikes, and it is deliberately unlike `fixture-service`: the primary quantity is a
file on disk, not a row in a queue, and the language is JavaScript, not Python.

It is **not** a commerce system: `ecommerce-cia`'s gate must fail here.

**Do not fix anything in this directory.** The answer key is `../EXPECTED-fixture-editor.md`,
outside this directory; the procedure is `../RUNBOOK.md`.

Run the tests: `node --test` (from this directory).

Operator commands: `node src/cli.js list`, `node src/cli.js open <id>`,
`node src/cli.js export <id> <dir>`. Restore an earlier version from the File menu (see
`docs/ARCHITECTURE.md` A3).

Layout:

```
config.json            configuration (data directory, autosave interval, backups, limits)
src/config.js          config.json over defaults; one shared object
src/store.js           load, save and list documents
src/autosave.js        the autosave timer and the per-document save status
src/render.js          the title-bar save badge, one renderer per state
src/thumbs.js          document thumbnails (display only, degrades per A4)
src/titles.js          file names for exported documents
src/backup.js          restore an earlier version of a document
src/cli.js             operator commands: list, open, export
tests/editor.test.js   the editor's tests
docs/ARCHITECTURE.md   the decisions the audit must respect
```
