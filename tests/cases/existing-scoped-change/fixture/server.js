'use strict';

const http = require('node:http');
const { authenticate, currentUser } = require('./auth');
const { listOrdersForUser } = require('./orders');

const PORT = Number(process.env.PORT) || 3000;

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(payload);
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

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === 'POST' && url.pathname === '/api/login') {
    const { username, password } = await readBody(req);
    const result = authenticate(username, password);
    if (!result) return json(res, 401, { error: 'invalid credentials' });
    return json(res, 200, { token: result.token, role: result.user.role });
  }

  if (req.method === 'GET' && url.pathname === '/api/orders') {
    const user = currentUser(req);
    if (!user) return json(res, 401, { error: 'not authenticated' });
    return json(res, 200, { orders: listOrdersForUser(user.id) });
  }

  return json(res, 404, { error: 'not found' });
});

if (require.main === module) {
  server.listen(PORT, '127.0.0.1', () => {
    process.stdout.write(`listening on http://127.0.0.1:${PORT}\n`);
  });
}

module.exports = { server };
