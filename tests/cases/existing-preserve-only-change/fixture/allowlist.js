'use strict';

const fs = require('fs');

const HOST = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/;

// One host per line. Blank lines and # comments are ignored.
function loadAllowedHosts(path) {
  const hosts = [];
  for (const raw of fs.readFileSync(path, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    if (!HOST.test(line)) continue;
    hosts.push(line);
  }
  return hosts;
}

module.exports = { loadAllowedHosts };
