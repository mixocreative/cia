'use strict';
// Restore an earlier version of a document from its backups (ARCHITECTURE A3).
const fs = require('node:fs/promises');
const path = require('node:path');
const config = require('./config');

async function restoreBackup(id, n = 1) {
  const file = path.join(config.dataDir, `${id}.json.bak${n}`);
  return JSON.parse(await fs.readFile(file, 'utf8'));
}

module.exports = { restoreBackup };
