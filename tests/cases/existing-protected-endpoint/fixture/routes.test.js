'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { listOrders } = require('./routes');

test('listOrders requires an authenticated user', () => {
  const res = {};
  listOrders({}, res);
  assert.equal(res.status, 401);
});

test('listOrders returns only the authenticated user orders', () => {
  const res = {};
  listOrders({ authenticatedUser: { id: 1 } }, res);
  assert.equal(res.status, 200);
  assert.deepEqual(res.body.orders.map((order) => order.id), [101, 102]);
});
