'use strict';

const { formatContextMode } = require('./context-mode');

function contextModeFlag(value) {
  return `--context-mode=${formatContextMode(value)}`;
}

module.exports = { contextModeFlag };
