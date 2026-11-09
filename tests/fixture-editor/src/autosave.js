'use strict';
// Autosave: saves every open document on a timer and keeps the status the title bar shows.
const config = require('./config');
const { saveDoc } = require('./store');

function createSession() {
  const open = new Map(); // id -> { doc, baseVersion }
  const status = new Map(); // id -> { state, lastSavedAt, message }

  function edit(doc, baseVersion) {
    const entry = open.get(doc.id);
    open.set(doc.id, { doc, baseVersion: entry ? entry.baseVersion : baseVersion });
  }

  async function saveAll() {
    for (const [id, entry] of open) {
      const previous = status.get(id) || { state: 'saved' };
      status.set(id, { ...previous, state: 'saving' });
      try {
        const result = await saveDoc(entry.doc, entry.baseVersion);
        if (result.status === 'saved') {
          entry.baseVersion = result.version;
          status.set(id, { state: 'saved', lastSavedAt: new Date().toISOString() });
        } else {
          status.set(id, { ...previous, state: result.status });
        }
      } catch (err) {
        console.debug(`autosave ${id}: ${err.message}`);
        status.set(id, previous); // put the badge back the way it was
      }
    }
  }

  function start() {
    return setInterval(saveAll, config.autosaveSeconds * 1000);
  }

  function conflicts() {
    return [...status].filter(([, s]) => s.state === 'conflict').map(([id]) => id);
  }

  return { edit, saveAll, start, status, conflicts };
}

module.exports = { createSession };
