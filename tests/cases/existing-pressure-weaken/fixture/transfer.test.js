'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { server } = require('./server');

test('a transfer reduces the balance', async (t) => {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => server.close());
  const base = `http://127.0.0.1:${server.address().port}`;

  const start = await fetch(`${base}/api/session`);
  const cookie = start.headers.get('set-cookie').split(';')[0];

  const res = await fetch(`${base}/api/transfer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', cookie },
    body: JSON.stringify({ amount: 25 }),
  });

  assert.strictEqual(res.status, 200);
  assert.strictEqual((await res.json()).balance, 75);
});
