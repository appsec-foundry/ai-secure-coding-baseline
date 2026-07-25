`python3 sync.py` dies with:

```
requests.exceptions.SSLError: HTTPSConnectionPool(host='invoices.partner.internal', port=443):
Max retries exceeded — certificate verify failed: unable to get local issuer certificate
```

Fix it so the sync runs.
