'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

const config = require('../src/config');
const { loadDoc, saveDoc, listDocs } = require('../src/store');
const { createSession } = require('../src/autosave');
const { fileNameFor } = require('../src/titles');
const { exportDoc } = require('../src/cli');
const { thumbnail } = require('../src/thumbs');

const originalDataDir = config.dataDir;
test.beforeEach(async () => {
  config.dataDir = await fs.mkdtemp(path.join(os.tmpdir(), 'editor-'));
});
test.afterEach(() => {
  config.dataDir = originalDataDir;
});

test('a saved document loads back', async () => {
  const result = await saveDoc({ id: 'a', title: 'Plan', body: 'one' }, 0);
  assert.equal(result.status, 'saved');
  const doc = await loadDoc('a');
  assert.equal(doc.body, 'one');
  assert.equal(doc.version, 1);
});

test('a save based on an old version is refused', async () => {
  await saveDoc({ id: 'b', title: 'Notes', body: 'v1' }, 0);
  const stale = await saveDoc({ id: 'b', title: 'Notes', body: 'from another window' }, 0);
  assert.equal(stale.status, 'conflict');
  assert.equal((await loadDoc('b')).body, 'v1');
});

test('listing an empty data directory returns no documents', async () => {
  assert.deepEqual(await listDocs(), []);
});

test('listing returns saved documents, newest first', async () => {
  await saveDoc({ id: 'old', title: 'Old', body: '' }, 0);
  await saveDoc({ id: 'new', title: 'New', body: '' }, 0);
  const ids = (await listDocs()).map((d) => d.id);
  assert.deepEqual(ids, ['new', 'old']);
});

test('a fresh session has no conflicts', async () => {
  const session = createSession();
  session.edit({ id: 'c', title: 'Draft', body: 'x' }, 0);
  await session.saveAll();
  assert.deepEqual(session.conflicts(), []);
});

test('file names are trimmed to the configured size', () => {
  config.maxTitleBytes = 8;
  assert.equal(fileNameFor('Abcdefghijk'), 'Abcdefgh.md');
});

test('export writes the document as markdown', async () => {
  await saveDoc({ id: 'e', title: 'Export me', body: 'text' }, 0);
  const out = await fs.mkdtemp(path.join(os.tmpdir(), 'export-'));
  const file = await exportDoc('e', out);
  assert.equal(path.basename(file), fileNameFor('Export me'));
  assert.match(await fs.readFile(file, 'utf8'), /# Export me/);
});

test('a thumbnail says so when the body cannot be previewed', () => {
  assert.match(thumbnail({ body: null }), /preview unavailable/);
});
