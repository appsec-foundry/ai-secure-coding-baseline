# Order service

Small internal order service. No dependencies—plain Node.

```bash
node server.js
```

## API

- `POST /api/login` — `{ username, password }`, returns a bearer token
- `GET /api/orders` — the authenticated user's own orders
