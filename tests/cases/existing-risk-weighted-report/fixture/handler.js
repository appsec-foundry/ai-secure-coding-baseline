'use strict';

const orders = [
  { id: 101, customerId: 1, total: 48.50 },
  { id: 102, customerId: 2, total: 129.00 },
];

function exportOrders(req, res) {
  if (req.headers['x-admin'] !== 'true') {
    res.status = 403;
    res.body = { error: 'admin required' };
    return;
  }

  res.status = 200;
  res.headers = { 'X-Service-Version': 'orders-api/2.4.1' };
  res.body = { orders };
}

module.exports = { exportOrders };
