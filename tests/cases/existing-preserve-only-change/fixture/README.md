# Webhook forwarder

Internal service that forwards events to customer webhooks. Only hosts on the
allow-list are ever contacted. No dependencies—plain Node.

```bash
ALLOWLIST_FILE=./allowed-hosts.txt node forward.js
```
