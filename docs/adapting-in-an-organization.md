# Adapting AISCB inside an organization

This guide shows how to add an organization's requirements, approved values,
and identity provider to AISCB without editing the baseline, then distribute
the result to developer machines, repositories, CI, and cloud agents.

The running example is Acme: browser frontends and HTTP APIs use Acme SSO, and
approved values live in internal blueprints. Replace the names with yours. This
is a recommendation, not part of the baseline.

## Recommended architecture

Keep five layers separate:

| Layer | Contains | How it is controlled |
| --- | --- | --- |
| AISCB baseline | The unchanged upstream rules | Pinned upstream release and digest |
| Organization overlay | Always-applicable rules, security invariants, and the routing mechanism | Reviewed like code; loaded with the baseline |
| Requirement packs | Actionable organization requirements and acceptance criteria | Loaded only when a compact route matches the work |
| Blueprints | Approved libraries, claim names, limits, headers, and patterns | Strict schema, compatibility version, reviewed changes |
| Tool adapters | The files each supported assistant actually loads | Generated from the other layers, never edited by hand |

The overlay may narrow AISCB but never relax it. Put an invariant in the overlay
when it must be present for every relevant task. Put detailed, task-specific
requirements in a requirement pack. Put approved values in a blueprint when a
rule can be stated completely without them. Examples:

- "Bind every protected query to the authenticated tenant" is an overlay rule.
- Detailed acceptance cases for tenant isolation belong in an API requirement
  pack.
- The tenant claim name and approved schema library are blueprint values.
- The approved group IDs and their permission mappings are blueprint values.

Do not force every organization requirement into an AISCB group. Use a
`narrows` mapping only when the requirement makes an AISCB rule more specific.
Keep requirements for an organization-only mechanism under their own stable ID.
This avoids misleading traceability and duplicate rule text.

Keep policy statements that name no mechanism outside the assistant
instructions. Enforce requirements that must always hold through application
controls, tests, CI, and runtime policy as well.

## What you need

Before you start, establish:

- an internal fork with protected review and merge rules;
- an owner for upstream merges, organization rules, and tool compatibility;
- an immutable release or internal package for each approved bundle;
- a way to verify release authenticity and integrity, such as a signed package
  or a pinned manifest with digests;
- device or package management for developer machines, where available;
- Python 3.10 or newer for the current installer and version helper;
- an explicit list of supported tools and operating systems; and
- a rollout, rollback, and inventory process.

The examples below use Unix paths. Use the platform's managed configuration and
atomic installation mechanism on Windows rather than translating shell snippets
literally.

## The result

The internal fork keeps sources, validators, and generated adapters together:

```text
acme/aiscb/
├── secure-coding-baseline.md          unchanged from upstream
├── acme-overlay.md                    Acme rules; imports AISCB where supported
├── requirements/
│   ├── catalog.yaml                   sources, mappings, routes, and ownership
│   └── packs/
│       ├── authentication.md          loaded only for matching work
│       └── tenant-isolation.md        loaded only for matching work
├── blueprints/
│   ├── schema.json                    strict schema for every blueprint
│   ├── spa.yaml                       approved browser values
│   └── api.yaml                       approved API values
├── scripts/
│   ├── build_bundle.py                validates and generates packs and adapters
│   └── install.py                     installs one verified bundle
└── dist/
    └── acme-sec-1.0.0/
        ├── manifest.json              IDs, compatibility, sizes, and digests
        ├── secure-coding-baseline.md
        ├── acme-overlay.md
        ├── requirements/              canonical requirement packs
        ├── blueprints/
        └── adapters/                  rendered instructions, routes, and skills
```

On a Unix developer machine, install each release into its own directory and
switch the complete bundle at once:

```text
~/.local/share/aiscb/
├── releases/
│   ├── acme-sec-0.9.0/
│   └── acme-sec-1.0.0/
└── current -> releases/acme-sec-1.0.0/
```

Verify every file before changing `current`. Keep the previous release until
the new one has passed local verification, so rollback does not require a
network request. Where symlinks are unsuitable, use the package manager or an
equivalent transactional directory replacement.

Substitute `<bundle-dir>` with the immutable release directory, such as
`~/.local/share/aiscb/releases/acme-sec-1.0.0`, never with `current`. A session
that loaded an older overlay will then continue to read requirement packs and
blueprints from the same release even if a managed update switches `current`
while the session is open.

## Step 1: Write the overlay

Give the overlay an independent ID rather than an `aiscb-0.1.10+acme` suffix.
It copies no AISCB text: AISCB remains unchanged and reports its own ID.

The overlay must:

- identify the AISCB groups a rule actually narrows, without inventing a
  mapping for organization-only requirements;
- contain every security-critical organization invariant;
- require applicable requirement packs to be loaded before affected work;
- stop affected work when a required pack or blueprint is missing, invalid, or
  incompatible;
- stop and report an ambiguity or conflict instead of asking the assistant to
  decide which natural-language rule is stricter; and
- use paths that the bundle builder replaces with verified absolute paths.

`acme-overlay.md` can look like this:

```markdown
@<bundle-dir>/secure-coding-baseline.md

# Acme Secure Coding Overlay

`baseline-id: acme-sec-1.0.0`. Extends AISCB (`aiscb-0.1.10`). Source: the
internal `acme/aiscb` repository. On the prompt `baseline?`, report both IDs
with the file each came from.

Where stated, these rules narrow AISCB; none relaxes it. If a rule conflicts
with AISCB, or an applicable requirement pack or blueprint is missing,
unreadable, invalid, or incompatible, stop the affected work and report the
problem. Do not invent a substitute or continue that work with AISCB alone.

- **[ACME-REQ-ROUTING-001] Requirement routing**: Before analysis, design, or
  implementation, match the work against the requirement packs advertised by
  the tool adapter. Load only every matching pack and its referenced
  blueprints. Do not load unrelated packs. A matching security-critical route
  whose pack cannot be loaded blocks the affected work.
- **[ACME-TENANT-001] Tenant isolation** (narrows AISCB-ACCESS-001): Every
  protected query binds the authenticated identity and tenant to the requested
  resource. Never accept the effective tenant or permissions from request
  data.
```

The explicit stop is important. Applying AISCB alone would be a fail-open when
the missing pack contains Acme's identity, tenant, or permission requirements.
Unrelated work that matches no missing pack may continue.

## Step 2: Add and map organization requirements

Use one requirement pack per coherent domain, not one file or skill per
requirement. Authentication, tenant isolation, browser security, and API
contracts are useful boundaries. A pack contains only instructions needed to
do and verify that kind of work; leave policy history, rationale, and full
control prose in the authoritative policy system.

Keep routing and traceability in `requirements/catalog.yaml`. For example:

```yaml
schema: acme-requirements/v1
packs:
  - id: ACME-PACK-AUTH-001
    file: packs/authentication.md
    description: >-
      Use for interactive sign-in, OIDC, sessions, roles, groups, or changes
      to authentication middleware. Do not use for unrelated API work.
    paths:
      - "src/auth/**"
      - "config/oidc/**"
    requirements:
      - id: ACME-SSO-001
        source: ACME-IAM-STD-12 section 4
        mapping:
          type: narrows
          targets: [AISCB-AUTH-001, AISCB-MECHANISMS-001]
      - id: ACME-IAM-AUDIT-001
        source: ACME-IAM-STD-12 section 7
        mapping:
          type: organization
```

`narrows` means that the organization rule makes the named AISCB rules more
specific. `organization` means that it stands on its own; it is not a weaker
mapping. Reject unknown mapping types, missing sources, duplicate IDs, invalid
AISCB targets, contradictory routes, and catalog entries whose pack is absent.
Several packs may legitimately match one task.

The referenced Markdown file is the canonical pack body. Give it stable
requirement IDs, actionable rules, required blueprint references, and positive
and negative acceptance cases. Do not repeat AISCB text. For example:

```markdown
# Acme authentication requirements

- **[ACME-SSO-001]** Use Acme SSO with authorization code and PKCE. Accept
  groups only from the validated `acme_groups` claim and map allow-listed group
  IDs to application permissions. Read and validate
  `<bundle-dir>/blueprints/spa.yaml` before implementation.
- **[ACME-IAM-AUDIT-001]** Emit the events named by the blueprint without
  credentials, tokens, or personal data not explicitly allowed there.

Verify successful SSO, invalid issuer and audience, unknown groups, missing
configuration, logout invalidation, and absence of secrets in logs.
```

Catalog descriptions are routing data, not a substitute for the pack body.
Keep the number of packs small and descriptions concise: assistants initially
see skill metadata, while the larger body is loaded only when selected. The
builder combines catalog metadata and the canonical body into native
`SKILL.md` files or a fallback route, so triggers have one source.

## Step 3: Add schema-validated blueprints

Blueprints contain approved values and implementation patterns, not behavioral
requirements; those belong in the overlay or a requirement pack. Keep
blueprints flat enough to review and strict enough to validate
deterministically. Reject unknown fields, invalid types, unsupported schema
versions, duplicate keys, and values outside their allow-lists.

This shortened `blueprints/spa.yaml` illustrates the boundary:

```yaml
# Acme SPA values for ACME-SPA-001.
# Mirrored from the internal source by CI; changes arrive through review.
schema: acme-spa/v1
overlay_major: 1
version: "2026-08-24"

auth:
  session_cookie:
    attributes: [HttpOnly, Secure, "SameSite=Lax", "Path=/"]

headers:
  content-security-policy: >
    default-src 'self'; script-src 'self'; style-src 'self';
    frame-ancestors 'none'; base-uri 'none'; object-src 'none'
  strict-transport-security: "max-age=31536000; includeSubDomains"
  enforced_by: application
```

The API blueprint can provide the tenant claim name, approved group-to-
permission mappings, accepted token values, schema library, body and page-size
limits, error shape, and permitted log fields. The overlay still states that
tenant binding, allow-listed permission mapping, and safe error handling are
mandatory.

Point overlay rules and requirement packs at files in the verified bundle, not
at URLs. A local file works offline and avoids treating an SSO page, proxy
response, or changed remote document as policy. Keep source URLs in metadata
used by the mirror job, not in instructions that ask an assistant to fetch
them.

## Step 4: Mirror an existing internal source

Prefer authoring blueprints in Git and generating the intranet view. This gives
you one reviewed source and no synchronization path.

If the intranet remains authoritative, a scheduled job may propose changes. It
must not publish them directly. Build the job from reviewed repository scripts,
not a long inline shell block. The scripts should:

1. fetch only from an exact HTTPS host and reject off-host redirects;
2. enforce connection timeouts and a response-size limit;
3. write to a temporary file;
4. validate UTF-8, YAML syntax, the strict schema, compatibility, and allowed
   values;
5. replace the working copy only after validation;
6. open or update one bot pull request when content changed; and
7. leave the last approved copy unchanged on every failure.

Pin external actions to reviewed commit SHAs. Install the validator's exact,
reviewed dependencies from a frozen file with hashes rather than relying on
packages preinstalled in a runner image. If the workflow uses `GITHUB_TOKEN` to
open a pull request, enable and review GitHub's **Allow GitHub Actions to create
and approve pull requests** repository setting.

Treat a blueprint change like a policy change when it affects authentication,
authorization, transport, secrets, or resource limits. Use a separate cadence
only for compatible value changes, and record the supported overlay major in
both the blueprint and bundle manifest.

## Step 5: Generate the tool adapters

The bundle builder, not a developer, creates the file each tool loads. Always
place the AISCB text before the overlay text when concatenation is required,
and remove the overlay's source import marker from that rendered adapter.

### Load requirement packs only when applicable

Keep only the baseline, compact overlay, and discovery metadata in the initial
context. Do not concatenate every requirement pack into `AGENTS.md`,
`CLAUDE.md`, or Copilot's repository-wide instructions, and do not import the
packs from `CLAUDE.md`: imports are resolved when instructions load and are not
lazy.

Prefer native Agent Skills. Their name and short description are available for
discovery, while the `SKILL.md` body is loaded when the skill is selected.
Render the same reviewed pack into the location expected by each tool:

| Tool | On-demand pack | Path-specific option |
| --- | --- | --- |
| Claude Code | `.claude/skills/<pack>/SKILL.md` | `.claude/rules/*.md` with `paths` |
| Codex | `.agents/skills/<pack>/SKILL.md` | Nested `AGENTS.md` only when directory scope fits |
| Copilot | `.github/skills/<pack>/SKILL.md` or `.agents/skills/<pack>/SKILL.md` | `.github/instructions/*.instructions.md` with `applyTo` |

Use path-specific instructions when a requirement maps reliably to files. Use
a skill description for semantic triggers such as "changes authentication" or
"adds a protected endpoint", because those can cross directories. Keep the
smallest non-negotiable invariant and trigger in the overlay when missing the
pack would create a material security risk; leave detailed rules, examples,
and tests in the pack.

For a supported surface without native skills, generate a compact fallback
route containing only domain, trigger, and verified pack path: absolute in a
local immutable bundle or repository-relative in a committed bundle. It tells
the assistant to read the matching pack before affected work. This is deferred
loading through an instruction, not a client guarantee, so verify it with
behavior tests. If a surface cannot read a pack on demand, select the applicable
packs when building the repository adapter instead of adding all of them.

Do not generate both a full route table and equivalent verbose skill
descriptions for the same adapter. Both come from `catalog.yaml`, but the
builder chooses the smallest discovery form the target supports. Set budgets
for always-loaded bytes, estimated tokens for each supported model, aggregate
skill descriptions, and each pack body. Fail generation on an unexpected
increase or duplicated requirement text.

### Claude Code

Claude Code supports imports from `CLAUDE.md`. For an organization-wide local
installation, deploy a managed-policy `CLAUDE.md` or import from another
root-managed, immutable path. Do not make managed policy import a user-writable
file in `~/.local/share`.

For a project adapter, a relative import can point at files committed in that
repository. For a user-level convenience install, an absolute import works, but
it is user-managed guidance rather than an enforced organization control.

Use `.claude/skills/` for semantic requirement packs and path-scoped
`.claude/rules/` where file patterns are sufficient. Claude loads imported
`CLAUDE.md` files eagerly, path-scoped rules when matching files are read, and
skill bodies on demand.

See Claude Code's documentation for
[instruction loading and imports](https://code.claude.com/docs/en/memory) and
[Agent Skills](https://code.claude.com/docs/en/slash-commands).

### Codex

Codex discovers `AGENTS.md` and does not document an import directive for it.
Generate one `AGENTS.md` containing the baseline followed by the overlay. Check
the rendered size against Codex's configured instruction limit; its documented
default combined limit is 32 KiB.

Install requirement packs as skills instead of appending their bodies. Codex
initially exposes skill metadata and loads the full instructions only when the
skill is used. Keep domain packs coarse and descriptions short because Codex
caps the initial skill metadata. Nested `AGENTS.md` files are useful for stable
directory scopes, but they do not replace semantic routing.

Codex builds its `AGENTS.md` instruction chain once per run. See the official
OpenAI documentation for
[custom instructions with `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md/)
and
[Agent Skills](https://developers.openai.com/codex/skills/).

### GitHub Copilot

Copilot CLI supports relative `@` references from `AGENTS.md`, `CLAUDE.md`, and
`.github/copilot-instructions.md`, but that behavior is not uniform across all
Copilot surfaces. Use an import only for a CLI-only adapter. Generate a combined
`.github/copilot-instructions.md` where repository-wide portability matters.

For deferred requirement loading, generate Agent Skills and path-specific
instruction files only for surfaces listed as supporting them. Check the
support matrix when adding or upgrading a Copilot surface; do not assume that
CLI behavior applies to IDE, coding agent, or code review.

See GitHub's documentation for
[Copilot CLI custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions),
[Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills),
and the
[custom-instructions support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

### Generated-file ownership

Track every generated adapter by the digest recorded in `manifest.json`.
Refuse to overwrite a file whose content does not match the last installed
digest. An interactive updater may offer to back it up and replace it after
confirmation; unattended updates should stop and report the drift.

Do not use the upstream single-`baseline-id` parser for a combined adapter. It
contains two IDs by design. Validate the source files separately, then verify
the generated adapter by its manifest digest.

## Step 6: Release and distribute one immutable bundle

Give each approved bundle an immutable version. Its manifest should include:

- the bundle and overlay IDs;
- the AISCB ID and exact upstream digest;
- the requirement catalog version, pack IDs, mappings, and digests;
- blueprint schema and compatibility versions;
- every installed path, size, and SHA-256 digest;
- the adapter generation version;
- measured always-loaded sizes and tool-specific token estimates; and
- the release provenance or package signature reference.

A protected branch controls ordinary merges, but it is not an immutable release
and `git pull --ff-only` is not an integrity check. It accepts any fast-forward
commit and gives a fresh clone no previously reviewed value to compare. Do not
replace release verification with a pull from a moving branch.

Prefer this distribution order:

1. signed internal package or device management for developer machines;
2. pinned bundle updates through bot pull requests for repositories used by CI
   and cloud agents; and
3. a manually verified installer only where neither is available.

Roll out to a small group first, retain the previous bundle, and make rollback a
single managed version change. Inventory the installed bundle through package
or device management; do not infer fleet state from assistant responses.

## Step 7: Update before the assistant starts

Do not pull instruction files from a session-start hook. Codex reads its
`AGENTS.md` chain once when the run starts, and Claude Code loads `CLAUDE.md` at
launch. A hook that updates files can therefore leave the current model context
on the previous version while a helper reads and reports the new disk version.

Apply updates before launching the assistant, through a managed package update,
a launcher wrapper, or a scheduled device-management task. If the network is
unavailable, keep the last verified bundle and report its age according to your
organization's staleness policy. Track the last attempt separately from the
last successful update so a failure does not cause a request at every session.

A session-start hook may report status, but label it precisely:

```text
AISCB bundle installed on disk: acme-sec-1.0.0
```

It must not claim that the same version is loaded into the model unless the tool
provides that evidence. Hooks should not modify the bundle they are reporting.

## Step 8: Adapt the upstream tooling

The current upstream installer manages one baseline file. `setup.sh` verifies
three bundle files: the baseline, installer, and version helper. A fork that
ships an overlay, requirement packs, and blueprints needs a bundle-oriented
implementation rather than a few additional copy calls.

Change the fork so that it:

- builds and validates all source files before generating adapters;
- authenticates the pinned or signed `manifest.json`, then verifies every
  bundled file before executing the installer;
- substitutes `<bundle-dir>` only in the installed overlay or generated
  adapter, never in the reviewed source;
- installs into a new versioned directory and switches the complete bundle;
- records every managed destination and digest for drift detection and
  uninstall;
- preserves foreign files and refuses symlink surprises;
- reports the installed bundle ID from the manifest rather than parsing a
  combined adapter; and
- removes or redirects the public GitHub release check if internal release
  inventory already supplies the expected version.

If you retain the upstream online release check, preserve all of its destination
checks: validate the URL before the request, reject off-host redirects, and
validate the final URL. Do not edit installed helper copies; ship, review, and
test the fork's source versions.

Add these checks to the suite run by `make check`:

- every `narrows AISCB-...` reference names a current AISCB group;
- requirement IDs and sources are present and unique across the catalog and
  packs;
- every catalog route resolves to its declared pack, every pack is cataloged,
  and each requirement's declared mapping matches its pack content;
- `organization` mappings have no invented AISCB target and `narrows` mappings
  have at least one valid target;
- native skill metadata and fallback routes are generated from the same
  catalog entries;
- every blueprint path resolves inside the bundle to a regular file;
- every blueprint passes the strict schema and compatibility checks;
- unknown or ambiguous values fail closed;
- every placeholder is replaced in generated output;
- generated adapters contain baseline then overlay exactly once and no
  unsupported source import marker;
- always-loaded adapters and skill metadata stay within their configured byte
  and token budgets, without duplicated requirement bodies;
- manifest sizes and digests match every file; and
- an interrupted install leaves the previous complete bundle active.

Use staged tests for installation, update, rollback, local drift, missing files,
invalid schemas, incompatible versions, and unavailable requirement packs on
every supported operating system.

## Step 9: Verify loading and behavior

Use four kinds of evidence:

1. **Installation:** verify the manifest, active bundle pointer, and managed
   destination digests.
2. **Tool loading:** inspect the tool's own diagnostics. Claude Code exposes
   loaded instruction files through `/context`; Copilot CLI exposes them through
   `/instructions`. Start a new Codex run after every update because it discovers
   `AGENTS.md` once per run. Then use `baseline?` as a cross-tool smoke test: it
   should name both IDs and their files.
3. **Lazy loading:** for each domain, verify that matching semantic and path
   triggers load the expected pack, unrelated work does not load it, and a
   missing required pack stops only affected work. Inspect context or tool
   traces where available, then confirm behavior because file visibility alone
   does not prove selection.
4. **Behavior:** run representative positive and negative cases for Acme SSO,
   missing packs and blueprints, invalid claims, cross-tenant access, browser
   policy, and limits. A correct ID response does not prove that the rules are
   followed.

Run these checks before promotion and after changes to an overlay, requirement
catalog or pack, blueprint, adapter generator, installer, or supported tool
version.

## Limits

The overlay changes what an assistant is told, not what the application
enforces. It cannot guarantee that a rule is followed or that every machine is
current. Managed permissions and hooks can enforce some tool behavior, but
application authorization, tests, CI gates, deployment policy, and runtime
controls remain necessary for security properties that must hold.
