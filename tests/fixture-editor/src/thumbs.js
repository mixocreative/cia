'use strict';
// Thumbnails for the document list. Display only; degrades per ARCHITECTURE A4.
const { escape } = require('./render');

function renderPreview(body) {
  const firstLines = body.split('\n').slice(0, 4).join('\n');
  return `<div class="thumb"><pre>${escape(firstLines.slice(0, 200))}</pre></div>`;
}

function thumbnail(doc) {
  try {
    return renderPreview(doc.body);
  } catch (err) {
    return '<div class="thumb muted">preview unavailable</div>';
  }
}

module.exports = { thumbnail };
