'use strict';

const { normalizeContextMode } = require('./context-mode');

function requestOptions(contextMode) {
  return { contextMode: normalizeContextMode(contextMode) };
}

module.exports = { requestOptions };
