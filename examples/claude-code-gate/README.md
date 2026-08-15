# Example: a deterministic gate under the baseline

The baseline is an instruction. An assistant that reads it can also skip it, and
nothing reports the gap. This directory shows what a check that runs outside the
model looks like — a Claude Code `PreToolUse` hook that refuses a small set of
edits and names the baseline rule it refused them under.

It is an example. It is not part of the baseline, it does not make the baseline
enforceable, and a project that installs it still needs review, secret scanning,
dependency scanning, and SAST. Copy it and change it; nothing here is meant to
be depended on as it is.

## Install

```bash
python3 examples/claude-code-gate/test_gate.py     # 9 rules, no model calls
```

Then merge `settings.example.json` into `.claude/settings.json` (project) or
`~/.claude/settings.json` (machine). Restart Claude Code, write
`requests.get(url, verify=False)` into a file, and the write is refused with the
rule id.

There is no environment variable that turns the gate off, on purpose. Remove the
hook from the settings file if you do not want it — that is a visible change to
a tracked file, unlike a flag someone sets once during a bad afternoon.

## What it denies

Nine patterns, each tied to the rule group it comes from:

| Rule | Denied |
| --- | --- |
| `AISEC-PRESERVE-001` | TLS verification off: `verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify: true`, `curl -k`, `NODE_TLS_REJECT_UNAUTHORIZED=0` |
| `AISEC-PRESERVE-001` | Auth or CSRF behind a switch: `SKIP_AUTH`, `DISABLE_CSRF`, `AUTH_ENABLED=false` |
| `AISEC-INPUT-001` | Unsafe deserializers: `yaml.load` without a loader, `pickle.loads`, `ObjectInputStream` |
| `AISEC-MECHANISMS-001` | A password through a fast digest: `sha256(password)`, `md5(pwd)` |
| `AISEC-MECHANISMS-001` | A token, key, or OTP from `Math.random()` or the `random` module |
| `AISEC-SECRETS-001` | Credential literals with a known prefix: `ghp_`, `sk-`, `AKIA`, `xoxb-`, `AIza`, PEM private keys |
| `AISEC-SECRETS-001` | Default credentials: `password = "changeme"`, `admin`, `letmein`, `123456` |
| `AISEC-DEFAULTS-001` | A wildcard CORS origin **together with** credentials |
| `AISEC-ENV-001` | `app.run(debug=True)`, `FLASK_DEBUG=1` |

Only the text an edit adds is scanned. Code that was already in the file is not
this edit's doing.

## What it deliberately does not deny

A gate that runs on every write fails in one way that matters: a wrong deny. The
user removes it from their settings, and the next hundred real findings never
happen. So anything that needs context to judge is missing here, even where the
pattern is easy to write:

- a bind to `0.0.0.0`, which is right in a container behind a TLS terminator and
  wrong on a laptop;
- SQL built with an f-string, which is routine for table names in a migration;
- MD5 over something that is not a password — cache keys, ETags, checksums;
- `@csrf_exempt`, which a webhook endpoint with signature verification uses
  legitimately;
- a new dependency, whose upstream a hook cannot verify.

Those belong in a second tier that asks instead of blocking, and pushes the
question back at the assistant: *which terminator?*, *how did you verify that
package?* This example does not implement that tier.

## What a hook cannot see at all

It sees one edit. Absence is invisible to it — whether the route just added has
an authorization check, whether the login endpoint is rate limited, whether the
session id rotates on login. Those are questions about the resulting state, so
they belong in a check over the diff, or in CI.

And the part of the baseline that matters most is not pattern-matchable in any
form: whether authorization binds the authenticated identity to the requested
resource, whether the change stayed in scope, whether a weakening went through
an explicit override with the user, whether the security note is honest.
`tests/cases/` covers that side, with a model and the uncertainty a model brings.

The gate and those cases answer different questions. The cases ask whether an
assistant follows the rules. The gate assumes it sometimes will not.

## Tests

`test_gate.py` checks three things, because a gate can fail in three independent
ways:

- every rule denies its sample **and** allows an ordinary sample — the second
  half is the one that keeps the gate installed;
- every rule id names a rule group that exists in `secure-coding-baseline.md`,
  so a renamed or retired id cannot survive as a finding nobody can look up;
- the hook contract works through a real process: a payload on stdin, a decision
  on stdout, exit 0 — including that a malformed payload is reported on stderr
  and allowed rather than blocking every edit in the session.

`make check` runs it.
