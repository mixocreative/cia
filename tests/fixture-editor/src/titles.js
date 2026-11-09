'use strict';
// File names for exported documents: the title, made safe for a file system and kept short.
const config = require('./config');

function fileNameFor(title) {
  const safe = String(title).replace(/[\\/:*?"<>|]/g, '-').trim() || 'Untitled';
  return Buffer.from(safe, 'utf8').subarray(0, config.maxTitleBytes).toString('utf8') + '.md';
}

module.exports = { fileNameFor };
