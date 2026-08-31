# Adapting AISCB inside an organization

A guide for adding an organization's own rules, blueprints, and identity provider to AISCB without editing the baseline, and for shipping the result to several hundred developers.

The running example is Acme: two application shapes (a browser frontend and an HTTP API), a corporate identity provider called Acme SSO, and blueprints that live in the intranet today. Replace the names with yours. This is a recommendation, not part of the baseline.

## What you need

Before you start, make sure these are in place.

- **A fork of this repository** on your internal Git hosting, with branch protection on the default branch. It is the source every developer machine and CI job installs from, so who can merge into it decides what the assistants are told.
- **Python 3.10 or newer** on every machine that runs the installer, and on every machine where the session-start hook runs. The installer and the version helper are both Python.
- **Git on developer machines**, if you distribute by clone rather than through an internal package or device management.
- **A writable home directory:** `~/.local/share/aiscb` for the managed files and `~/.config/aiscb` for the installer's state.
- **A decision on which tools you support.** The installer covers Claude Code, Codex, and GitHub Copilot. Surfaces that read no file from disk, such as Copilot organization custom instructions, need the text pasted in and are outside the installer's reach.
- **An owner.** Someone has to follow upstream releases, merge them into the fork, and re-run `make check` after each merge. Without that the fork silently freezes on an old baseline.

The guide assumes a user-level install on developer machines (`--user`), plus a committed copy in the repositories that CI and cloud agents work in.

## The result

Two directory layouts describe the whole setup: what you maintain in Git, and what ends up on a developer machine.

The internal fork:

```
acme/aiscb/                          internal fork
├── secure-coding-baseline.md        unchanged from upstream
├── acme-overlay.md                  Acme rules, imports the baseline
├── blueprints/
│   ├── spa.yaml                     values for browser frontends
│   └── api.yaml                     values for HTTP APIs
└── scripts/install.py               places the files, wires the imports
```

A developer machine after installation:

```
~/.local/share/aiscb/
├── secure-coding-baseline.md        loaded on every session
├── acme-overlay.md                  loaded on every session
├── blueprints/                      read only when a rule points here
├── install.py                       the installer keeps its own copy here
└── show-baseline-version.py         and the version helper beside it
~/.claude/CLAUDE.md                  one import line, pointing at the overlay
```

Baseline and overlay are in context in every session: the baseline's roughly 4,000 tokens plus a few hundred for the overlay. The blueprints cost nothing until a rule sends the assistant to them.

## Step 1: Sort your material

Most of what an organization calls a secure coding standard does not belong in an overlay. Sort it first:

| Material | Example at Acme | Where it goes |
| --- | --- | --- |
| Rule naming a mechanism | "Validate `iss`, `aud`, `exp` against the configured issuer" | overlay |
| Values and reference data | claim names, CSP, cookie attributes, page-size limits | blueprint YAML |
| Everything else | "Applications must be secure by design" | policy handbook, CI, review |

The test for the first column is the one the baseline applies to itself: name a mechanism, not a goal.

## Step 2: Write the overlay

The overlay is a second instruction file loaded next to the baseline. Four properties make it an overlay rather than a second opinion:

- its own `baseline-id`, so `baseline?` reports both layers with their files;
- it narrows AISCB rules and never relaxes one;
- it fails closed when a file it references is missing;
- every rule names the AISCB group it narrows, so the link survives an upstream release.

Give the overlay an independent ID rather than an `aiscb-0.1.10+acme` suffix: it copies no AISCB rule text, and the baseline ships unchanged and keeps reporting its own ID beside it.

Write paths as `<install-dir>` and let the installer substitute the real directory when it places the file, so the file in Git stays machine-independent.

`acme-overlay.md` then looks like this — the first line is the import that pulls the baseline in, and each rule below names the AISCB group it narrows:

```markdown
@<install-dir>/secure-coding-baseline.md

# Acme Secure Coding Overlay

`baseline-id: acme-sec-1.0.0`. Extends AISCB (`aiscb-0.1.10`). Source: the internal `acme/aiscb` repository. On the prompt `baseline?`, report both IDs with the file each came from.

These rules narrow the AISCB rules; they never relax one. Where they conflict, the stricter rule applies and the conflict is reported. If a file referenced here is missing or unreadable, the AISCB rule applies alone and the gap is reported; do not continue on your own judgement.

- **[ACME-SSO-001] Interactive sign-in** (narrows AISCB-AUTH-001, AISCB-MECHANISMS-001): Interactive user sign-in goes through Acme SSO using the OIDC authorization-code flow with PKCE and the `acme-oidc` library. Issuer, client ID, and audience come from configuration; startup fails when one is absent. Validate the signature, `iss`, `aud`, and `exp` against the configured issuer and accept `RS256` only. Roles come from the `acme_groups` claim, never from request data or a local role table. No local password fallback, no implicit flow, no client secret in the repository.
- **[ACME-SPA-001] Browser frontends** (narrows AISCB-DEFAULTS-001): Before you write or change authentication, token, cookie, CSP, header, or CORS code in a browser frontend, read `<install-dir>/blueprints/spa.yaml` and follow it. The blueprint makes these rules concrete; it overrides none of them. Deviate only where AISCB or this overlay requires it, and report the deviation.
- **[ACME-API-001] HTTP interfaces** (narrows AISCB-ACCESS-001, AISCB-INPUT-001, AISCB-LIMITS-001, AISCB-ERRORS-001): Before you add an endpoint or change its authentication, authorization, input validation, limits, or error output, read `<install-dir>/blueprints/api.yaml` and follow it. The same conditions as in ACME-SPA-001 apply.
```

The two pointer rules are the part worth copying carefully:

- the trigger names concrete code, not a project category, because an assistant recognizes "I am writing cookie code" more reliably than "this is an SPA";
- the installed file carries a spelled-out absolute path, so nothing has to be constructed;
- the blueprint may make a rule concrete but never lift it;
- the fail-closed sentence keeps a missing file from becoming improvisation.

## Step 3: Add the blueprints

A blueprint holds the values the overlay rule points at. Keep it flat and readable — the assistant reads it as text, so structure it for a human reviewer.

This is `blueprints/spa.yaml`, shortened:

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
  - "'unsafe-inline' or 'unsafe-eval' in the CSP"
  - client-side role checks as the only check
```

`blueprints/api.yaml` has the same shape: accepted algorithms and claims, the tenant binding every query must apply, the schema library, body and page-size limits, the error format, and the mandatory and forbidden log fields.

Point the rule at a local path, not a URL. An assistant that fetches a URL sees a 200 with text and cannot tell a blueprint from an SSO login page, a proxy error, or yesterday's version. A local file also works offline, in CI, and behind a proxy that does not know the intranet host. The URL belongs in the blueprint header and in the job that fetches it.

Where nothing lands on disk, such as Copilot organization custom instructions, put the handful of values that matter into the instruction text instead of linking to them.

## Step 4: Load it

The overlay is the entry point and imports the baseline, so nobody ends up with the narrowing rules but not the rules they narrow.

In Claude Code that means one line in `~/.claude/CLAUDE.md`, with an absolute path — a relative import resolves against the importing file's directory:

```markdown
@/home/<user>/.local/share/aiscb/acme-overlay.md
```

Upstream writes that line only when `~/.claude/CLAUDE.md` does not exist yet. If the file is already there, the installer refuses to touch it and reports the line to add by hand. Most developers who have used Claude Code for a while have that file, so plan for the case: have your fork's installer append the line to an existing file (after checking it is not already present), or push a managed-policy `CLAUDE.md` through device management and skip the user file.

`AGENTS.md` and `.github/copilot-instructions.md` cannot import at all. For Codex and Copilot, write one generated file instead, baseline first, overlay second. Regenerate it on every update and include it in the installer's drift detection, or a local edit goes unnoticed.

That generated file also needs its own tracking. Upstream symlinks both paths to the baseline and identifies a managed file by its single `baseline-id` line; a concatenation carries two, which the parser rejects, so every scan skips the file silently. Track it by content digest instead, and replace the symlink step for these two tools with a write that refuses to overwrite a file it did not generate.

Verify by asking the tool `baseline?`. The answer names both IDs and their files. That is the only check that both layers are loaded.

## Step 5: Keep the blueprints current

Best case: author the YAML in Git, review changes as pull requests, generate the intranet page from it. One source, no sync.

If the intranet page stays the source, mirror it into Git on a schedule. The job below fetches one blueprint, checks it parses, and opens a pull request when the content changed:

```yaml
# .github/workflows/mirror-blueprints.yml
on:
  schedule: [{cron: "0 5 * * *"}]
permissions:
  contents: write
  pull-requests: write
jobs:
  mirror:
    runs-on: ubuntu-latest
    env:
      SPA_URL: https://intranet.acme.example/appsec/spa/spa.yaml
      GH_TOKEN: ${{ github.token }}
    steps:
      - uses: actions/checkout@<commit sha you verified>
      - run: |
          curl --proto '=https' --fail --silent --show-error \
               --max-time 30 --max-filesize 65536 \
               --output blueprints/spa.yaml "$SPA_URL"
          python3 -c "import yaml; yaml.safe_load(open('blueprints/spa.yaml'))"
          git diff --quiet && exit 0
          git config user.name aiscb-mirror
          git config user.email aiscb-mirror@acme.example
          git switch -c mirror-blueprints
          git commit -am "blueprints: mirror spa.yaml"
          git push -u origin mirror-blueprints
          gh pr create --fill
```

The job runs with a service credential, not a developer's. Its value is not freshness but review: a wiki edit becomes a commit with a diff and a history, so the page's edit permissions stop being the security boundary of your coding standard. When the fetch fails, the job fails and the last good copy stays.

Write the YAML by hand once, from the existing blueprints. Do not derive it from the HTML page automatically.

## Step 6: Distribute and update

Two audiences: developer machines, and the agents in CI and the cloud that never see one.

Where software distribution exists, use it. An internal package turns an update into a version bump; a managed-policy `CLAUDE.md` pushed by device management turns it into a file replacement.

Otherwise use Git. Commit the files into the project repositories and update them with bot pull requests, which CI and cloud agents need anyway. For developer machines, clone once to a fixed path and let a session-start hook refresh it. This script pulls at most once a day, gives up after five seconds, and stays silent when anything fails:

```sh
# <install-dir>/refresh.sh — once a day, with a timeout, failing quietly
stamp=~/.local/share/aiscb/.last-pull
[ -n "$(find "$stamp" -mtime -1 2>/dev/null)" ] || {
  timeout 5 git -C ~/.local/share/aiscb pull --ff-only --quiet 2>/dev/null && touch "$stamp"
}
```

Register it in the same hook list the version hook uses rather than inventing a place of its own. In Claude Code that list lives in `~/.claude/settings.json`:

```json
{"hooks": {"SessionStart": [
  {"matcher": "startup|resume|fork",
   "hooks": [{"type": "command", "command": "sh",
              "args": ["<install-dir>/refresh.sh"], "timeout": 5}]}
]}}
```

For Claude Code and Codex the upstream installer appends its entry to that list instead of replacing it, so a refresh entry you added survives an install run. The Copilot hook file, `~/.copilot/hooks/aiscb-baseline-version.json`, is owned as a whole: any content the installer did not write makes it refuse the file and skip the version hook. Extend that file inside the fork's installer instead of adding a second entry to it.

Split the cadence: rules ride with the package or release, blueprints refresh on their own so a small correction does not trigger a full rollout.

### How the update path works today

After installation the version hook is the only moving part, so it is worth knowing exactly what it does before changing it.

The guided setup offers the hook and writes it when the developer accepts. A plain `install.py --user` run copies the helper into the data directory but registers no hook at all — if you roll out non-interactively, your fork's installer has to register it. For a user-level install the entry is:

```json
{"matcher": "startup|resume|fork",
 "hooks": [{"type": "command", "command": "python3",
            "args": ["/home/<user>/.local/share/aiscb/show-baseline-version.py",
                     "--output", "json"], "timeout": 5}]}
```

At every session start the helper prints `AI Secure Coding Baseline active: aiscb-0.1.10` as a system message and exits. It reads the installed baseline file and nothing else, and it makes no network request.

The update notice is opt-in and comes from a cache, not from the hook. When setup enables it, `~/.config/aiscb/installations.json` carries `update_check.enabled: true`. The helper then compares the installed ID against the cached `update_check.latest`, appends `Update ... available` when the cached release is newer, and — at most once every 24 hours — starts `install.py --refresh-update-cache` as a detached background process. That process queries `api.github.com`, writes the new `latest` into the registry, and exits. The session never waits for it, so a notice appears one session after a release, not in the session that triggered the lookup.

Nothing on this path installs anything. Upstream only notifies, because applying a change from a public source automatically would let a compromised source rewrite the rules on every machine silently — which is also why the bootstrap pins a commit and its hashes. Applying an update means running the verified Quick start again.

### What the fork changes

Internally the source is yours and the trust decision happens once, when the change is merged, so applying updates automatically is reasonable. Keep four conditions:

- apply only from the internal protected source;
- never overwrite a locally modified managed file, back it up and report instead;
- replace files atomically, so no session reads a half-written one;
- log what changed, so a behavior change can be explained afterwards.

Two details in the hook itself need work in a fork:

- **The helper reports one ID.** It looks for `secure-coding-baseline.md` beside or one level above itself and requires exactly one `baseline-id` line in it. The overlay never appears in the startup message. Extending the helper means shipping your own version of that file, not editing the installed copy: the installer replaces a placed helper only when its digest matches one it shipped, and its "hook configured" check compares the placed file against its own source.
- **The release check is pinned to `api.github.com`** in three places in `install.py` — the URL check before the request, the redirect handler, and the check on the final URL after redirects. Pointing the check at internal hosting means changing all three. If your rollout already carries the version, drop the check instead.

None of this tells you who is running an old copy. A CI job comparing the version committed in a repository against the current one does.

## Step 7: Adjust the tooling

`scripts/install.py` places one baseline file, with its own copy and the version helper beside it, and `setup.sh` verifies exactly three bundle files. Your fork needs both to work on a list, and needs the overlay's placeholder replaced with the real directory as the file is written:

```python
BASELINE = "secure-coding-baseline.md"
OVERLAY  = "acme-overlay.md"
BUNDLE   = [BASELINE, OVERLAY, "blueprints/spa.yaml", "blueprints/api.yaml"]

# The overlay is what each tool loads; the real directory replaces the placeholder
text = overlay_text.replace("<install-dir>", str(data_root))
```

Both target maps have to move to the overlay as well. Upstream keeps them separate — `project_targets()` links `.claude/rules/<file>` inside a repository, `user_targets()` links `~/.claude/<file>` and adds the import line to `~/.claude/CLAUDE.md`. Swap the linked file in both, and keep the import line pointing at the overlay.

The file list is the smaller half of the work. Three parts of the installer identify a file by its single `baseline-id` line, and none of them fits the new files:

- the placement check that refuses a foreign occupant reads that line, so the blueprints need an identity of their own, such as a schema check or a digest comparison;
- the scans that find unmanaged copies read it too, which is why the generated Codex and Copilot file stays invisible until you track it by digest;
- update state, registry digest, and uninstall each key off one installed file and have to carry the list.

You can drop the hash pinning internally. It exists because the public bootstrap downloads from raw URLs nobody reviews. A protected internal repository covers the same attack with less machinery: `--ff-only` refuses a rewritten history, and branch protection decides what enters the branch. It is not the same guarantee — nothing compares the content against a value you reviewed earlier — so keep the pinning wherever the remote is not protected.

Finally, add a check to the suite `make check` runs (`tests/selfcheck.py`), so a narrowing rule cannot point at an AISCB group that no longer exists after an upstream merge:

```python
ids = set(re.findall(r"\[(AISCB-[A-Z]+-\d+)\]", baseline))
for ref in re.findall(r"narrows ([A-Z0-9\-, ]+)", overlay):
    missing = {i.strip() for i in ref.split(",")} - ids
    assert not missing, f"unknown AISCB ID: {missing}"
```

A second check that every blueprint path in the overlay resolves to a file keeps the pointers from rotting.

## Limits

The overlay changes what an assistant is told, not what it does. It cannot guarantee that a blueprint was read, that a rule was followed, or that every developer runs the current version. Keep review, CI, gates, and runtime controls for anything that must hold.
