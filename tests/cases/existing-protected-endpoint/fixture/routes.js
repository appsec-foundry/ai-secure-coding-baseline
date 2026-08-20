'use strict';

const { authenticatedUser } = require('./auth');
const { listOrdersForUser } = require('./orders');

function sendJson(res, status, body) {
  res.status = status;
  res.body = body;
}

function listOrders(req, res) {
  const user = authenticatedUser(req);
  if (!user) return sendJson(res, 401, { error: 'not authenticated' });
  return sendJson(res, 200, { orders: listOrdersForUser(user.id) });
}

module.exports = { listOrders };
