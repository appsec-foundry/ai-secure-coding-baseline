# Adapting AISCB inside an organization

This guide explains how to add organization-specific rules and approved values
without changing AISCB itself. The result can be distributed consistently to
developer machines, repositories, CI, and cloud agents.

The examples use Acme, Acme SSO, and internal blueprints. Replace these names
with your own. This guide is a recommendation, not part of the baseline.

## The model

Keep five parts separate:

| Part | Purpose |
| --- | --- |
| AISCB baseline | Unchanged upstream rules, pinned to an approved release |
| Organization overlay | Small set of rules that always apply |
| Requirement packs | Detailed instructions and acceptance criteria, loaded only for matching work |
| Blueprints | Approved values such as libraries, claim names, limits, headers, and mappings |
| Tool adapters | Generated files in the format each assistant loads |

This separation keeps the instructions small and maintainable:

- Put an invariant in the overlay when it must always be visible. For example:
  every protected query must bind the authenticated tenant.
- Put detailed rules and test cases in a requirement pack, grouped by a useful
  domain such as authentication, tenant isolation, browser security, or APIs.
- Put approved values in a blueprint when the rule can be understood without
  them. Examples include a tenant claim name or approved group mappings.
- Use an AISCB mapping only when an organization rule genuinely makes an AISCB
  rule more specific. Give organization-only requirements their own stable IDs.

The overlay may narrow AISCB but must never relax it. Instructions also do not
replace application controls: enforce requirements that must always hold with
tests, CI, permissions, deployment policy, or runtime controls.

## Before you start

Assign owners for upstream updates, organization requirements, and supported
tools. Use an internal repository with protected review, publish each approved
bundle as an immutable release, and verify its signature or pinned file
digests. Define supported tools and operating systems, then prepare a staged
rollout, rollback, and inventory process.

Use managed package or device management where possible. The current AISCB
installer and version helper require Python 3.10 or newer. The examples below
use Unix paths; on Windows, use the platform's managed and transactional
installation mechanism instead of translating shell commands literally.

An approved bundle contains the unchanged AISCB file, the overlay, requirement
catalog and packs, blueprints, generated tool adapters, and a manifest with
versions and digests. Install releases side by side and switch the whole bundle
atomically, for example:

```text
~/.local/share/aiscb/
├── releases/acme-sec-0.9.0/
├── releases/acme-sec-1.0.0/
└── current -> releases/acme-sec-1.0.0/
```

Verify all files before switching `current`, and keep the previous release for
offline rollback. Generated paths must point to the immutable release directory,
not `current`; otherwise an open session could combine files from two releases.

## 1. Create a small organization overlay

Give the overlay its own ID, such as `acme-sec-1.0.0`, while AISCB keeps its
original ID and content. Do not copy AISCB rules into the overlay.

The overlay must:

- state which rules narrow AISCB and which stand alone;
- contain every security-critical organization invariant;
- require matching requirement packs and blueprints to be loaded before work;
- stop affected work if required content is missing, invalid, incompatible,
  ambiguous, or conflicting; and
- use bundle paths that the build process replaces with verified absolute paths.

A compact overlay can look like this:

```markdown
@<bundle-dir>/secure-coding-baseline.md

# Acme Secure Coding Overlay

`baseline-id: acme-sec-1.0.0`. Extends AISCB (`aiscb-0.1.10`). On `baseline?`,
report both IDs and their source files.

These rules may narrow AISCB but never relax it. If a conflict exists, or an
applicable pack or blueprint is unavailable or invalid, stop the affected work
and report the problem. Do not invent a substitute.

- **[ACME-REQ-ROUTING-001]** Load every requirement pack matching the task and
  its blueprints before affected work. Do not load unrelated packs.
- **[ACME-TENANT-001]** (narrows AISCB-ACCESS-001): Bind every protected query
  to the authenticated identity and tenant. Never take effective tenant or
  permissions from request data.
```

Stopping only the affected work matters: continuing without required identity
or permission rules would fail open, while unrelated work can still proceed.

## 2. Add requirement packs and routing

Use one pack per coherent domain rather than one file per requirement. Keep
policy history and rationale in the authoritative policy system; packs should
contain only the instructions and acceptance criteria needed to do the work.

Maintain a catalog that records each pack's ID, file, owner, source, concise
trigger description, optional path triggers, and requirement mappings. Use two
mapping types:

- `narrows`: the organization requirement makes named AISCB rules more specific;
- `organization`: the requirement stands alone and has no invented AISCB target.

Several packs may match one task. Validation must reject missing sources,
duplicate IDs, unknown mapping types, invalid AISCB targets, contradictory
routes, and missing or uncataloged packs.

Each pack should contain stable requirement IDs, actionable rules, referenced
blueprints, and representative positive and negative tests. Do not repeat AISCB
text. For example:

```markdown
# Acme authentication requirements

- **[ACME-SSO-001]** Use Acme SSO with authorization code and PKCE. Accept
  groups only from the validated `acme_groups` claim and map only approved group
  IDs. Validate `<bundle-dir>/blueprints/spa.yaml` before implementation.
- **[ACME-IAM-AUDIT-001]** Emit the events named by the blueprint without
  credentials, tokens, or unapproved personal data.

Verify successful SSO, invalid issuer and audience, unknown groups, missing
configuration, logout invalidation, and absence of secrets in logs.
```

Keep the number of packs small and trigger descriptions short. The catalog is
the single source for generated skill metadata and fallback routes; its summary
does not replace the full pack.

## 3. Store approved values in blueprints

Blueprints hold approved values and patterns, not behavioral requirements.
Examples include cookie attributes, headers, claim names, group-to-permission
mappings, token values, schema libraries, request and page limits, error shapes,
and permitted log fields.

Give every blueprint a strict schema and compatibility version. Reject unknown
fields, invalid types, duplicate keys, unsupported versions, and values outside
their allow-lists. Keep the overlay or pack responsible for saying what is
mandatory; the blueprint supplies the approved value.

Point instructions to verified files inside the bundle, not to live URLs. This
keeps work available offline and prevents a changed page or proxy response from
becoming policy. Source URLs belong in mirror-job metadata.

Prefer maintaining blueprints in Git and generating the intranet view. If the
intranet must remain authoritative, use a scheduled job to propose changes
instead of publishing them directly. The reviewed job must fetch only from an
allowed HTTPS host, reject off-host redirects, enforce time and size limits,
validate content and compatibility in a temporary file, and open one pull
request only when valid content changed. Every failure leaves the last approved
copy untouched. Pin external CI actions and install exact, reviewed dependencies
from a frozen file with hashes.

Treat changes affecting authentication, authorization, transport, secrets, or
resource limits like policy changes. Faster updates are suitable only for
compatible values, with the supported overlay major recorded in the blueprint
and bundle manifest.

## 4. Generate adapters for each tool

Generate adapters from the reviewed baseline, overlay, catalog, packs, and
blueprints; do not edit generated files by hand. When a tool needs one combined
file, place AISCB before the overlay and remove the overlay's import marker.

Keep only AISCB, the compact overlay, and discovery metadata in the initial
context. Load detailed packs only when their semantic or path triggers match.
Prefer native Agent Skills for semantic triggers and path-scoped instructions
for reliable directory or file-pattern matches.

| Tool | On-demand packs | Path-specific option |
| --- | --- | --- |
| Claude Code | `.claude/skills/<pack>/SKILL.md` | `.claude/rules/*.md` with `paths` |
| Codex | `.agents/skills/<pack>/SKILL.md` | Nested `AGENTS.md` when directory scope fits |
| Copilot | `.github/skills/` or `.agents/skills/` | `.github/instructions/*.instructions.md` with `applyTo` |

When a supported surface cannot load skills, generate a compact route with the
domain, trigger, and verified pack path. If it cannot read a pack on demand,
select the applicable packs when building that repository's adapter. Verify
deferred loading with behavior tests; an instruction to load later is not a
client guarantee.

Do not duplicate a full route table in verbose skill descriptions. Set size and
token budgets for always-loaded content, discovery metadata, and each pack, and
fail generation on unexpected growth or repeated requirement text.

Tool-specific points:

- **Claude Code:** use managed-policy `CLAUDE.md` or another root-managed,
  immutable path for organization-wide enforcement. Relative imports suit
  committed project files; user-level absolute imports are convenience, not an
  organization control. Imports load eagerly, while skills load on demand.
- **Codex:** generate an `AGENTS.md` containing AISCB followed by the overlay;
  Codex has no documented import directive for this file. Keep it within the
  configured instruction limit and install packs as skills. Codex discovers its
  `AGENTS.md` chain once per run.
- **GitHub Copilot:** relative imports are not uniform across all surfaces. Use
  them only for a verified CLI-only adapter; otherwise generate combined
  repository instructions. Check the support matrix for each enabled surface.

Relevant documentation: [Claude Code instructions](https://code.claude.com/docs/en/memory)
and [skills](https://code.claude.com/docs/en/slash-commands),
[Codex `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md/) and
[skills](https://developers.openai.com/codex/skills/), and the GitHub Copilot
[custom-instructions support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

Record each generated adapter's digest in the manifest. Refuse to overwrite a
locally changed adapter automatically; an interactive updater may offer backup
and replacement after confirmation. Validate source files separately because a
combined adapter intentionally contains two baseline IDs, then verify the
generated file against its manifest digest.

## 5. Release and distribute the bundle

Publish each approved bundle under an immutable version. Its manifest records:

- bundle, overlay, and AISCB IDs, plus the exact upstream digest;
- catalog, pack, blueprint, schema, and compatibility versions and digests;
- every installed path, file size, and SHA-256 digest;
- adapter-generator version and measured instruction budgets; and
- release provenance or package-signature reference.

A protected branch is not an immutable release, and pulling from a moving
branch is not an integrity check. Prefer signed internal packages or device
management for developer machines, pinned bundle updates through bot pull
requests for repositories used by CI or cloud agents, and a manually verified
installer only when neither is available.

Roll out to a small group first, retain the previous bundle, and make rollback
a single managed version change. Use package or device management for inventory;
an assistant's version response does not prove fleet state.

## 6. Update before starting the assistant

Apply updates through package management, a launcher, or a scheduled device
task before the assistant starts. Do not update instruction files from a
session-start hook: tools may already have loaded the previous version while a
helper reports the new disk version.

If the network is unavailable, retain the last verified bundle and report its
age according to your staleness policy. Track the last attempt separately from
the last successful update. A startup hook may report only what it knows, for
example `AISCB bundle installed on disk: acme-sec-1.0.0`; it must not claim that
the same version is loaded into the model.

## 7. Extend the upstream tooling

The upstream installer manages one baseline file. A bundle with an overlay,
packs, blueprints, and adapters needs a bundle-oriented installer that:

- validates sources before generating adapters;
- authenticates the manifest and verifies every file before executing anything;
- substitutes bundle paths only in installed or generated output;
- installs a new versioned directory and switches the complete bundle atomically;
- tracks managed destinations and digests for drift detection and uninstall;
- preserves unrelated files and rejects unsafe symlink destinations; and
- reports the manifest's bundle ID instead of parsing a combined adapter.

If the fork keeps the upstream online release check, preserve its URL,
redirect, and destination validation. Ship reviewed helper sources instead of
editing installed copies. Remove or redirect that check when internal release
inventory already provides the expected version.

Automated checks should cover catalog and mapping consistency, valid AISCB
references, unique requirement IDs and sources, complete routes, strict
blueprint schemas and compatibility, safe bundle paths, replaced placeholders,
correct adapter ordering, size and token budgets, manifest digests, and atomic
installation. Test install, update, rollback, interruption, local drift,
missing or incompatible content, and unavailable packs on every supported OS.

## 8. Verify installation, loading, and behavior

Use four kinds of evidence before promotion and after changes to the overlay,
catalog, packs, blueprints, generator, installer, or supported tool versions:

1. **Installation:** verify the manifest, active release, and destination
   digests.
2. **Tool loading:** inspect the tool's diagnostics where available. Start a new
   Codex run after an update. Use `baseline?` as a cross-tool smoke test; the
   response should name both IDs and source files.
3. **Pack selection:** confirm that semantic and path triggers load the expected
   pack, unrelated tasks do not, and a missing required pack stops only affected
   work.
4. **Behavior:** run representative positive and negative cases for SSO, claims,
   tenant isolation, browser policy, limits, and missing or invalid content.

A correct ID response proves only that the assistant can see the instructions,
not that it follows them. File visibility alone likewise does not prove that a
pack was selected.

## Limits

An overlay changes what an assistant is told; it cannot guarantee compliance or
that every machine is current. Keep application authorization, tests, CI gates,
deployment policy, and runtime controls in place for every property that must
hold.
