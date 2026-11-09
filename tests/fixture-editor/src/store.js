'use strict';
// Document store: one JSON file per document under config.dataDir.
const fs = require('node:fs/promises');
const path = require('node:path');
const config = require('./config');

function docPath(id) {
  return path.join(config.dataDir, `${id}.json`);
}

// Load a document. A document that does not exist yet is a new, empty one.
async function loadDoc(id) {
  try {
    const raw = await fs.readFile(docPath(id), 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    console.debug(`load ${id}: ${err.message}; starting a new document`);
    return { id, title: 'Untitled', body: '', version: 0 };
  }
}

// Save a document. `baseVersion` is the version the editor loaded; a save based on an older
// version than the one on disk is refused (ARCHITECTURE A2).
async function saveDoc(doc, baseVersion) {
  const current = await loadDoc(doc.id);
  if (current.version !== baseVersion) {
    return { status: 'conflict', version: current.version };
  }
  const next = { ...doc, version: current.version + 1, savedAt: new Date().toISOString() };
  await fs.mkdir(config.dataDir, { recursive: true });
  await fs.writeFile(docPath(doc.id), JSON.stringify(next, null, 2));
  return { status: 'saved', version: next.version };
}

// The newest documents for the start screen (ARCHITECTURE A5).
async function listDocs() {
  let names;
  try {
    names = await fs.readdir(config.dataDir);
  } catch (err) {
    if (err.code === 'ENOENT') return []; // nothing saved yet
    throw err;
  }
  const docs = [];
  for (const name of names.filter((n) => n.endsWith('.json'))) {
    docs.push(JSON.parse(await fs.readFile(path.join(config.dataDir, name), 'utf8')));
  }
  docs.sort((a, b) => (a.savedAt < b.savedAt ? 1 : -1));
  return docs.slice(0, config.recentLimit);
}

module.exports = { loadDoc, saveDoc, listDocs, docPath };
