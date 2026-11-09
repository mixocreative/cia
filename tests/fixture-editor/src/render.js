'use strict';
// The title-bar save badge: one renderer per save state.

function escape(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
}

const BADGES = {
  saved: (s) => `<span class="badge ok">Saved ${escape(s.lastSavedAt || '')}</span>`,
  saving: () => '<span class="badge busy">Saving…</span>',
  offline: () => '<span class="badge warn">Offline — changes are kept on this computer</span>',
  error: (s) => `<span class="badge err">Not saved: ${escape(s.message || 'unknown error')}</span>`,
};

function badge(status) {
  const render = BADGES[status.state];
  return render ? render(status) : '';
}

function titleBar(doc, status) {
  return `<header><h1>${escape(doc.title)}</h1>${badge(status)}</header>`;
}

module.exports = { badge, titleBar, escape };
