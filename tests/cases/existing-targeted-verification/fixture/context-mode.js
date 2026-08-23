'use strict';

const MODES = new Set(['compact', 'full']);

function normalizeContextMode(value) {
  const mode = value === undefined ? 'compact' : value;
  if (!MODES.has(mode)) {
    throw new TypeError(`invalid context mode: ${mode}`);
  }
  return mode;
}

function formatContextMode(value) {
  return normalizeContextMode(value);
}

module.exports = { formatContextMode, normalizeContextMode };
