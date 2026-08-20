'use strict';

const orders = [
  { id: 101, userId: 1, item: 'Desk lamp' },
  { id: 102, userId: 1, item: 'Notebook' },
  { id: 103, userId: 2, item: 'Monitor stand' },
];

function listOrdersForUser(userId) {
  return orders.filter((order) => order.userId === userId);
}

function findOrderForUser(orderId, userId) {
  return orders.find((order) => order.id === orderId && order.userId === userId) || null;
}

module.exports = { listOrdersForUser, findOrderForUser };
