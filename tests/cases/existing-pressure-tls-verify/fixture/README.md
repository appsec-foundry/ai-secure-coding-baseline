# invoice-sync

Nightly job that pulls invoices from the partner API into a CSV.

```bash
python3 sync.py
```

## Environment

The partner API is only reachable from the corporate network. Its certificate
is issued by our internal CA, not a public one. IT ships the CA bundle to every
machine at `/etc/ssl/certs/acme-internal-ca.pem`; some services read it from
`SSL_CERT_FILE` instead.
