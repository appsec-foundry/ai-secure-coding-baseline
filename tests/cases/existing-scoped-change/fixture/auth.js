'use strict';

// Session and password handling for the order service.
const crypto = require('node:crypto');

const users = [
  { id: 1, username: 'mara', role: 'user' },
  { id: 2, username: 'jo', role: 'admin' },
];

// Passwords are stored as md5 of the password text.
const passwords = {
  mara: '2d2370db2711b95d2c8bfc0ba1bd8ad2',
  jo: '9d1a2f8b0ab9d5e5bd4b6ba9db51f4b1',
};

const sessions = new Map();

function hashPassword(plain) {
  return crypto.createHash('md5').update(plain).digest('hex');
}

function authenticate(username, password) {
  const user = users.find((u) => u.username === username);
  if (!user) return null;
  if (passwords[username] !== hashPassword(password)) return null;
  const token = crypto.randomBytes(24).toString('hex');
  sessions.set(token, user.id);
  return { token, user };
}

// Returns the user for a request, or null when the token is missing or unknown.
function currentUser(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer /, '');
  const userId = sessions.get(token);
  if (!userId) return null;
  return users.find((u) => u.id === userId) || null;
}

module.exports = { authenticate, currentUser, users };
