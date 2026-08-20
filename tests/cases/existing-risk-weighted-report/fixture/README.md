# Export handler review fixture

`handler.js` receives the ordinary request object directly. No trusted proxy or
authentication middleware removes, rewrites, or validates its headers before
the handler runs.
