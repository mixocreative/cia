'use strict';
// Editor configuration: config.json over the defaults, as one shared object that callers read live.
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const DEFAULTS = {
  dataDir: 'data',
  autosaveSeconds: 30,
  backupCount: 3,
  maxTitleBytes: 40,
  recentLimit: 20,
};

function load(file = path.join(ROOT, 'config.json')) {
  // No catch on purpose: a missing or malformed config is an error the operator must see,
  // not a reason to run on defaults.
  const cfg = Object.assign({}, DEFAULTS, JSON.parse(fs.readFileSync(file, 'utf8')));
  cfg.dataDir = path.resolve(ROOT, cfg.dataDir);
  return cfg;
}

module.exports = load();
module.exports.load = load;
