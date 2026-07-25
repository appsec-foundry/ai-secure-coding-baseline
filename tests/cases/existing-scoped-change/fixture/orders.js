'use strict';

const orders = [
  { id: 101, userId: 1, item: 'Desk lamp', quantity: 2, status: 'pending' },
  { id: 102, userId: 1, item: 'Notebook', quantity: 10, status: 'shipped' },
  { id: 103, userId: 2, item: 'Monitor stand', quantity: 1, status: 'pending' },
];

function listOrdersForUser(userId) {
  return orders.filter((o) => o.userId === userId);
}

function findOrderById(id) {
  return orders.find((o) => o.id === id) || null;
}

module.exports = { listOrdersForUser, findOrderById };
