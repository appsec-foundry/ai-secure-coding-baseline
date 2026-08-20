'use strict';

// The outer application sets this value only after verifying its server-side
// session. Route handlers use this accessor rather than request identifiers.
function authenticatedUser(req) {
  const user = req.authenticatedUser;
  if (!user || !Number.isSafeInteger(user.id) || user.id <= 0) return null;
  return { id: user.id };
}

module.exports = { authenticatedUser };
