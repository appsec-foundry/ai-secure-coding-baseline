'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const {normalizeLabel} = require('./normalize');

test('normalizes case and surrounding whitespace', () => {
  assert.equal(normalizeLabel('  Ready  '), 'ready');
});
