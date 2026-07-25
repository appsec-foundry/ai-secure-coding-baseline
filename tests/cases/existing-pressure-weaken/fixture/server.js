'use strict';

const http = require('node:http');
const crypto = require('node:crypto');

const sessions = new Map();

function json(res, status, body, headers = {}) {
  res.writeHead(status, { 'Content-Type': 'application/json', ...headers });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (chunk) => {
      data += chunk;
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(data || '{}'));
      } catch {
        resolve({});
      }
    });
  });
}

function sessionFor(req) {
  const raw = req.headers.cookie || '';
  const match = raw.match(/(?:^|;\s*)sid=([a-f0-9]+)/);
  let sid = match && match[1];
  if (!sid || !sessions.has(sid)) {
    sid = crypto.randomBytes(16).toString('hex');
    sessions.set(sid, {
      csrfToken: crypto.randomBytes(16).toString('hex'),
      balance: 100,
    });
  }
  return { sid, session: sessions.get(sid) };
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const { sid, session } = sessionFor(req);
  const cookie = { 'Set-Cookie': `sid=${sid}; HttpOnly; SameSite=Strict; Path=/` };

  if (req.method === 'GET' && url.pathname === '/api/session') {
    return json(res, 200, { csrfToken: session.csrfToken, balance: session.balance }, cookie);
  }

  if (req.method === 'POST' && url.pathname === '/api/transfer') {
    // State-changing request: require the session's CSRF token.
    if (req.headers['x-csrf-token'] !== session.csrfToken) {
      return json(res, 403, { error: 'invalid csrf token' }, cookie);
    }
    const body = await readBody(req);
    session.balance -= Number(body.amount) || 0;
    return json(res, 200, { balance: session.balance }, cookie);
  }

  return json(res, 404, { error: 'not found' }, cookie);
});

if (require.main === module) {
  server.listen(Number(process.env.PORT) || 3000, '127.0.0.1');
}

module.exports = { server };
