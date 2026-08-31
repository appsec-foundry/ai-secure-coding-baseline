# Adapting AISCB inside an organization

A guide for adding an organization's own rules, blueprints, and identity provider to AISCB without editing the baseline, and for shipping the result to several hundred developers.

The running example is Acme: two application shapes (a browser frontend and an HTTP API), a corporate identity provider called Acme SSO, and blueprints that live in the intranet today. Replace the names with yours. This is a recommendation, not part of the baseline.

## The result

```
acme/aiscb/                          internal fork
├── secure-coding-baseline.md        unchanged from upstream
├── acme-overlay.md                  Acme rules, imports the baseline
├── blueprints/
│   ├── spa.yaml                     values for browser frontends
│   └── api.yaml                     values for HTTP APIs
└── scripts/install.py               places the files, wires the imports
```

On a developer machine after installation:

```
~/.local/share/aiscb/{secure-coding-baseline.md,acme-overlay.md,blueprints/}
~/.claude/CLAUDE.md                  one import line, pointing at the overlay
```

Always in context: baseline plus overlay, about 4,400 tokens. The blueprints are read only when a rule sends the assistant to them.

## Step 1: Sort your material

| Material | Example at Acme | Where it goes |
| --- | --- | --- |
| Rule naming a mechanism | "Validate `iss`, `aud`, `exp` against the configured issuer" | overlay |
| Values and reference data | claim names, CSP, cookie attributes, page-size limits | blueprint YAML |
| Everything else | "Applications must be secure by design" | policy handbook, CI, review |

The test for the first column is the one the baseline applies to itself: name a mechanism, not a goal.

## Step 2: Write the overlay

The overlay is a second instruction file loaded next to the baseline. Four things make it an overlay rather than a second opinion:

- its own `baseline-id`, so `baseline?` reports both layers with their files;
- it narrows AISCB rules and never relaxes one;
- it fails closed when a file it references is missing;
- every rule names the AISCB group it narrows, so the link survives an upstream release.

`acme-overlay.md`:

```markdown
@/home/<user>/.local/share/aiscb/secure-coding-baseline.md

# Acme Secure Coding Overlay

`baseline-id: acme-sec-1.0.0`. Extends AISCB (`aiscb-0.1.10`). Source: the internal `acme/aiscb` repository. On the prompt `baseline?`, report both IDs with the file each came from.

These rules narrow the AISCB rules; they never relax one. Where they conflict, the stricter rule applies and the conflict is reported. If a file referenced here is missing or unreadable, the AISCB rule applies alone and the gap is reported; do not continue on your own judgement.

- **[ACME-SSO-001] Interactive sign-in** (narrows AISCB-AUTH-001, AISCB-MECHANISMS-001): Interactive user sign-in goes through Acme SSO using the OIDC authorization-code flow with PKCE and the `acme-oidc` library. Issuer, client ID, and audience come from configuration; startup fails when one is absent. Validate the signature, `iss`, `aud`, and `exp` against the configured issuer and accept `RS256` only. Roles come from the `acme_groups` claim, never from request data or a local role table. No local password fallback, no implicit flow, no client secret in the repository.
- **[ACME-SPA-001] Browser frontends** (narrows AISCB-DEFAULTS-001): Before you write or change authentication, token, cookie, CSP, header, or CORS code in a browser frontend, read `/home/<user>/.local/share/aiscb/blueprints/spa.yaml` and follow it. The blueprint makes these rules concrete; it overrides none of them. Deviate only where AISCB or this overlay requires it, and report the deviation.
- **[ACME-API-001] HTTP interfaces** (narrows AISCB-ACCESS-001, AISCB-INPUT-001, AISCB-LIMITS-001, AISCB-ERRORS-001): Before you add an endpoint or change its authentication, authorization, input validation, limits, or error output, read `/home/<user>/.local/share/aiscb/blueprints/api.yaml` and follow it. The same conditions as in ACME-SPA-001 apply.
```

Four details in the pointer rules do the work:

- the trigger names concrete code, not a project category, because an assistant recognizes "I am writing cookie code" more reliably than "this is an SPA";
- the path is spelled out, so nothing has to be constructed;
- the blueprint may make a rule concrete but never lift it;
- the fail-closed sentence keeps a missing file from becoming improvisation.

## Step 3: Add the blueprints

`blueprints/spa.yaml`, shortened:

```yaml
# Acme SPA security blueprint - material for ACME-SPA-001.
# Mirrored from https://intranet.acme.example/appsec/spa by CI. Do not edit here.
blueprint: acme-spa
version: 2026-08-24

auth:
  flow: oidc-authorization-code-pkce
  library: acme-oidc
  token_storage: memory only; never localStorage or sessionStorage
  session_cookie:
    attributes: [HttpOnly, Secure, "SameSite=Lax", "Path=/"]

headers:
  content-security-policy: >
    default-src 'self'; script-src 'self'; style-src 'self';
    frame-ancestors 'none'; base-uri 'none'; object-src 'none'
  strict-transport-security: "max-age=31536000; includeSubDomains"
  enforced_by: application; the ingress sets none of these headers

forbidden:
  - dangerouslySetInnerHTML and comparable raw HTML sinks
  - 'unsafe-inline' or 'unsafe-eval' in the CSP
  - client-side role checks as the only check
```

`blueprints/api.yaml` has the same shape: accepted algorithms and claims, the tenant binding every query must apply, the schema library, body and page-size limits, the error format, and the mandatory and forbidden log fields.

Point the rule at a local path, not a URL. An assistant that fetches a URL sees a 200 with text and cannot tell a blueprint from an SSO login page, a proxy error, or yesterday's version. A local file also works offline, in CI, and behind a proxy that does not know the intranet host. The URL belongs in the blueprint header and in the job that fetches it.

Where nothing lands on disk, such as Copilot organization custom instructions, put the handful of values that matter into the instruction text instead of linking to them.

## Step 4: Load it

The overlay is the entry point and imports the baseline, so nobody ends up with the narrowing rules but not the rules they narrow. In Claude Code, the installer writes one line into `~/.claude/CLAUDE.md`:

```markdown
@/home/<user>/.local/share/aiscb/acme-overlay.md
```

Use absolute paths for a user-level install; a relative import resolves against the importing file's directory.

`AGENTS.md` and `.github/copilot-instructions.md` cannot import. For Codex and Copilot the installer writes one generated file, baseline first, overlay second. Regenerate it on every update and include it in the installer's drift detection, or a local edit goes unnoticed.

Verify by asking the tool `baseline?`. The answer names both IDs and their files. That is the only check that both layers are loaded.

## Step 5: Keep the blueprints current

Best: author the YAML in Git, review changes as pull requests, generate the intranet page from it. One source, no sync.

If the intranet stays the source, mirror it:

```yaml
# .github/workflows/mirror-blueprints.yml
on:
  schedule: [{cron: "0 5 * * *"}]
jobs:
  mirror:
    steps:
      - run: |
          curl --proto '=https' --fail --silent --max-filesize 65536 \
               --output blueprints/spa.yaml "$SPA_URL"
          python3 -c "import yaml; yaml.safe_load(open('blueprints/spa.yaml'))"
          git diff --quiet || gh pr create --fill
```

The job runs with a service credential, not a developer's. Its value is not freshness but review: a wiki edit becomes a commit with a diff and a history, so the page's edit permissions stop being the security boundary of your coding standard. When the fetch fails, the job fails and the last good copy stays.

Write the YAML by hand once, from the existing blueprints. Do not derive it from the HTML page automatically.

## Step 6: Distribute and update

Two audiences: developer machines, and the agents in CI and the cloud that never see one.

Where software distribution exists, use it. An internal package turns an update into a version bump; a managed-policy `CLAUDE.md` pushed by device management turns it into a file replacement.

Otherwise use Git. Commit the files into the project repositories and update them with bot pull requests, which CI and cloud agents need anyway. For developer machines, clone once to a fixed path and let the session-start hook refresh it:

```sh
# once a day, with a timeout, failing quietly
stamp=~/.local/share/aiscb/.last-pull
[ -n "$(find "$stamp" -mtime -1 2>/dev/null)" ] || {
  timeout 5 git -C ~/.local/share/aiscb pull --ff-only --quiet 2>/dev/null && touch "$stamp"
}
```

Split the cadence: rules ride with the package or release, blueprints refresh on their own so a small correction does not trigger a full rollout.

Apply updates automatically. The public installer only notifies because a compromised public source would otherwise change the rules on every machine silently, which is why the bootstrap pins a commit and its hashes. Internally the source is yours and the trust decision happens once, when the change is merged. Keep four conditions:

- apply only from the internal protected source;
- never overwrite a locally modified managed file, back it up and report instead;
- replace files atomically, so no session reads a half-written one;
- log what changed, so a behavior change can be explained afterwards.

None of this tells you who is running an old copy. A CI job comparing the version committed in a repository against the current one does.

## Step 7: Adjust the tooling

`scripts/install.py` places exactly one filename and `setup.sh` verifies exactly three bundle files. Your fork needs both to work on a list:

```python
BASELINE = "secure-coding-baseline.md"
OVERLAY  = "acme-overlay.md"
BUNDLE   = [BASELINE, OVERLAY, "blueprints/spa.yaml", "blueprints/api.yaml"]

# Claude Code links the overlay; the real directory replaces the placeholder
"claude": [("link", root / ".claude" / "rules" / OVERLAY)],
text = overlay_text.replace("<install-dir>", str(data_root))
```

Internally you can drop the hash pinning. It exists because the public bootstrap downloads from raw URLs nobody reviews; a protected internal repository pulled with `--ff-only` gives the same guarantee with less machinery.

Add one check to `make check`, so a narrowing rule cannot point at an AISCB group that no longer exists:

```python
ids = set(re.findall(r"\[(AISCB-[A-Z]+-\d+)\]", baseline))
for ref in re.findall(r"narrows ([A-Z0-9\-, ]+)", overlay):
    missing = {i.strip() for i in ref.split(",")} - ids
    assert not missing, f"unknown AISCB ID: {missing}"
```

A second check that every blueprint path in the overlay resolves to a file keeps the pointers from rotting.

## Limits

The overlay changes what an assistant is told, not what it does. It cannot guarantee that a blueprint was read, that a rule was followed, or that every developer runs the current version. Keep review, CI, gates, and runtime controls for anything that must hold.
