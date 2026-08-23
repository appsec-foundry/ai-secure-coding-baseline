'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');
const {
  formatContextMode,
  normalizeContextMode,
} = require('../context-mode');

test('normalizeContextMode defaults to compact', () => {
  assert.equal(normalizeContextMode(), 'compact');
});

test('normalizeContextMode accepts compact', () => {
  assert.equal(normalizeContextMode('compact'), 'compact');
});

test('normalizeContextMode accepts full', () => {
  assert.equal(normalizeContextMode('full'), 'full');
});

test('normalizeContextMode rejects an invalid value', () => {
  assert.throws(() => normalizeContextMode('automatic'), /invalid context mode/);
});

test('formatContextMode formats compact', () => {
  assert.equal(formatContextMode('compact'), 'compact');
});

test('formatContextMode formats full', () => {
  assert.equal(formatContextMode('full'), 'full');
});
