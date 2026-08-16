'use strict';

const https = require('https');
const { loadAllowedHosts } = require('./allowlist');

const allowed = loadAllowedHosts(process.env.ALLOWLIST_FILE || './allowed-hosts.txt');

function forward(target, payload) {
  const url = new URL(target);
  if (url.protocol !== 'https:' || !allowed.includes(url.hostname)) {
    throw new Error('destination not allowed');
  }
  const req = https.request(url, { method: 'POST', timeout: 5000 });
  req.end(JSON.stringify(payload));
}

module.exports = { forward };
