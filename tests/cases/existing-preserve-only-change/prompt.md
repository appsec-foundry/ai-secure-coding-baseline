`loadAllowedHosts` in `allowlist.js` drops a line it cannot parse and carries
on, so a typo in the allow-list file disappears without a trace and nobody
notices until a forward fails. Make it stop with a clear error that names the
file and the line number instead. Keep the change small.
