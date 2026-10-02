// Exercise the actual browser script with controlled responses and a minimal DOM.
// No packages are required; run: node --test sentinel/tests/review_ui.test.cjs
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const { runInNewContext } = require('node:vm');

function element() {
  return {
    value: '', textContent: '', hidden: false, disabled: false,
    listeners: {}, children: [],
    classList: { add() {}, toggle() {} },
    addEventListener(name, handler) { this.listeners[name] = handler; },
    replaceChildren() { this.children = []; },
    append(...children) { this.children.push(...children); },
  };
}
function evidence(id, revision = 0, status = 'open') {
  return {
    synthetic: true, links: {}, legacy_action: { status: 'synthetic_no_action' },
    case: {
      id, revision, status, finding: {}, observation: { raw: {} },
      conflicts: [], history: [],
    },
  };
}
function response(body, status = 200) {
  return { ok: status === 200, status, json: async () => body };
}
function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}
function desk(detail, post = async () => response({})) {
  const elements = new Map();
  const get = (id) => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  get('disposition').value = 'insufficient_evidence';
  const payloads = [];
  const context = {
    document: { getElementById: get, createElement: element, querySelectorAll: () => [] },
    crypto: { randomUUID: () => `request_${payloads.length + 1}` },
    setInterval() {},
    fetch: async (path, options) => {
      if (options?.method === 'POST') {
        payloads.push(JSON.parse(options.body));
        return post(path, options);
      }
      if (path === '/api/status') return response({
        health: { status: 'synthetic' }, counts: {}, policy: {},
      });
      if (path.startsWith('/api/cases?')) return response({ items: [], total: 0 });
      return response(await detail(path.split('/').at(-1)));
    },
  };
  runInNewContext(readFileSync(join(__dirname, '../review/static/app.js'), 'utf8'), context);
  return {
    get, payloads, open: context.openCase,
    submit: () => get('decision-form').listeners.submit({ preventDefault() {} }),
  };
}

test('stale revision reload retains the note and selected disposition', async () => {
  let revision = 1;
  const ui = desk((id) => evidence(id, revision, 'acknowledged'),
    async () => response({ detail: 'Stale revision; reload case' }, 409));
  await ui.open('case_a');
  ui.get('operator').value = 'Automated fixture tester';
  ui.get('note').value = 'Evidence needs independent verification';
  ui.get('disposition').value = 'expected_activity';
  await ui.submit();
  revision = 2;
  await ui.open('case_a');
  assert.equal(ui.get('note').value, 'Evidence needs independent verification');
  assert.equal(ui.get('disposition').value, 'expected_activity');
  assert.match(ui.get('detail-meta').textContent, /Revision 2/);
});

test('different cases retain separate drafts and default disposition', async () => {
  const ui = desk((id) => evidence(id, 1, 'acknowledged'));
  await ui.open('case_a');
  ui.get('note').value = 'Draft A';
  ui.get('disposition').value = 'policy_breach';
  await ui.open('case_b');
  assert.equal(ui.get('note').value, '');
  assert.equal(ui.get('disposition').value, 'insufficient_evidence');
  ui.get('note').value = 'Draft B';
  await ui.open('case_a');
  assert.equal(ui.get('note').value, 'Draft A');
  assert.equal(ui.get('disposition').value, 'policy_breach');
  await ui.open('case_b');
  assert.equal(ui.get('note').value, 'Draft B');
});

test('delayed older reads cannot replace the last selected case', async () => {
  const slow = deferred();
  const ui = desk((id) => id === 'case_a' ? slow.promise : evidence(id));
  const first = ui.open('case_a');
  await ui.open('case_b');
  slow.resolve(evidence('case_a'));
  await first;
  assert.equal(ui.get('detail-title').textContent, 'Case case_b');
  assert.equal(ui.get('export-json').href, '/api/cases/case_b/export/json');
});

test('retry reuses its idempotency key and successful save clears the draft', async () => {
  let saved = false;
  let attempts = 0;
  const ui = desk((id) => evidence(id, saved ? 1 : 0, saved ? 'acknowledged' : 'open'),
    async () => {
      attempts += 1;
      if (attempts === 1) throw new Error('Network interrupted');
      saved = true;
      return response({});
    });
  await ui.open('case_a');
  ui.get('operator').value = 'Automated fixture tester';
  ui.get('note').value = 'Inspected synthetic receipt';
  await ui.submit();
  assert.equal(ui.get('note').value, 'Inspected synthetic receipt');
  await ui.submit();
  assert.equal(ui.payloads[0].request_id, ui.payloads[1].request_id);
  assert.equal(ui.get('note').value, '');
  assert.match(ui.get('detail-meta').textContent, /Revision 1/);
  await ui.open('case_b');
  await ui.open('case_a');
  assert.equal(ui.get('note').value, '');
});

test('a loading case and duplicate submits cannot dispatch another decision', async () => {
  const slow = deferred();
  const save = deferred();
  const ui = desk((id) => id === 'case_b' ? slow.promise : evidence(id),
    async () => save.promise);
  await ui.open('case_a');
  ui.get('operator').value = 'Automated fixture tester';
  ui.get('note').value = 'Draft A';
  const loading = ui.open('case_b');
  await ui.submit();
  assert.equal(ui.payloads.length, 0);
  slow.resolve(evidence('case_b'));
  await loading;
  ui.get('note').value = 'Draft B';
  const saving = ui.submit();
  assert.equal(ui.get('note').disabled, true);
  await ui.submit();
  assert.equal(ui.payloads.length, 1);
  save.resolve(response({}));
  await saving;
  assert.equal(ui.get('note').disabled, false);
});
