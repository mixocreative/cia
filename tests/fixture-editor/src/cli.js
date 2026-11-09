'use strict';
// Operator commands: list, open <id>, export <id> <dir>.
const fs = require('node:fs/promises');
const path = require('node:path');
const { loadDoc, listDocs } = require('./store');
const { fileNameFor } = require('./titles');

async function exportDoc(id, dir) {
  const doc = await loadDoc(id);
  const target = path.join(dir, fileNameFor(doc.title));
  const tmp = `${target}.tmp`;
  await fs.writeFile(tmp, `# ${doc.title}\n\n${doc.body}\n`);
  await fs.rename(tmp, target); // a reader never sees half an export
  return target;
}

async function main(argv) {
  const [cmd, ...args] = argv;
  if (cmd === 'list') {
    for (const doc of await listDocs()) console.log(`${doc.id}\tv${doc.version}\t${doc.title}`);
    return 0;
  }
  if (cmd === 'open' && args[0]) {
    console.log(JSON.stringify(await loadDoc(args[0]), null, 2));
    return 0;
  }
  if (cmd === 'export' && args.length === 2) {
    console.log(await exportDoc(args[0], args[1]));
    return 0;
  }
  console.error('usage: cli.js list | open <id> | export <id> <dir>');
  return 2;
}

if (require.main === module) {
  main(process.argv.slice(2)).then((code) => process.exit(code));
}

module.exports = { exportDoc, main };
