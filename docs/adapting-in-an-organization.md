# Adapting aiscb inside an organization

This guide shows how to add organization-specific rules and approved values
without changing aiscb, then distribute them consistently.

The examples use Acme, Acme SSO, and internal blueprints. Replace these names
with your own. This guide is a recommendation, not part of the baseline.

## The model

Keep five parts separate:

| Part | Purpose |
| --- | --- |
| aiscb baseline | Unchanged upstream rules, pinned to an approved release |
| Organization overlay | Small set of rules that always apply |
| Requirement packs | Detailed instructions and acceptance criteria, loaded only for matching work |
| Blueprints | Approved values such as libraries, claim names, limits, headers, and mappings |
| Tool adapters | Generated files in the format each assistant loads |

Use each part for one kind of content:

- Put invariants that must always be visible in the overlay.
- Put detailed rules and test cases in a requirement pack, grouped by a useful
  domain such as authentication, tenant isolation, browser security, or APIs.
- Put approved values in a blueprint when the rule can be understood without
  them. Examples include a tenant claim name or approved group mappings.
- Use an aiscb mapping only when an organization rule genuinely makes an aiscb
  rule more specific. Give organization-only requirements their own stable IDs.

The overlay may narrow aiscb but never relax it. Enforce properties that must
hold with application controls, tests, CI, or deployment policy as well.

## Before you start

Assign owners for upstream updates, organization requirements, and tool
support. Review bundles in a protected repository, publish immutable releases,
and verify them by signature or pinned digests. Define rollout, rollback, and
inventory for each supported tool and operating system.

Use managed package or device management where possible. The current aiscb
installer and version helper require Python 3.10 or newer. The examples below
use Unix paths; on Windows, use the platform's managed and transactional
installation mechanism instead of translating shell commands literally.

Bundle the unchanged aiscb file, overlay, requirement catalog and packs,
blueprints, generated adapters, and a versioned manifest. Install releases side
by side and switch atomically, for example:

```text
~/.local/share/aiscb/
├── releases/acme-sec-0.9.0/
├── releases/acme-sec-1.0.0/
└── current -> releases/acme-sec-1.0.0/
```

Verify the bundle before switching `current` and retain the previous release.
Generated paths must point to the immutable release, not `current`, so a running
session cannot mix releases.

## 1. Create a small organization overlay

Give the overlay its own ID, such as `acme-sec-1.0.0`, while aiscb keeps its
original ID and content. Do not copy aiscb rules into the overlay.

The overlay must:

- state which rules narrow aiscb and which stand alone;
- contain every security-critical organization invariant;
- require matching requirement packs and blueprints to be loaded before work;
- stop affected work if required content is missing, invalid, incompatible,
  ambiguous, or conflicting; and
- use bundle paths that the build process replaces with verified absolute paths.

A compact overlay can look like this:

```markdown
@<bundle-dir>/secure-coding-baseline.md

# Acme Secure Coding Overlay

`baseline-id: acme-sec-1.0.0`. Extends aiscb (`aiscb-0.1.10`). On `baseline?`,
report both IDs and their source files.

These rules may narrow aiscb but never relax it. If a conflict exists, or an
applicable pack or blueprint is unavailable or invalid, stop the affected work
and report the problem. Do not invent a substitute.

- **[ACME-REQ-ROUTING-001]** Load every requirement pack matching the task and
  its blueprints before affected work. Do not load unrelated packs.
- **[ACME-TENANT-001]** (narrows aiscb-ACCESS-001): Bind every protected query
  to the authenticated identity and tenant. Never take effective tenant or
  permissions from request data.
```

This stops work that lacks required policy without blocking unrelated work.

## 2. Add requirement packs and routing

Use one pack per domain. Keep history and rationale in the policy system; packs
need only actionable instructions and acceptance criteria.

Maintain a catalog that records each pack's ID, file, owner, source, concise
trigger description, optional path triggers, and requirement mappings. Use two
mapping types:

- `narrows`: the organization requirement makes named aiscb rules more specific;
- `organization`: the requirement stands alone and has no invented aiscb target.

Several packs may match. Reject missing sources or packs, duplicate IDs,
unknown mapping types, invalid aiscb targets, contradictory routes, and
uncataloged packs.

Each pack should contain stable requirement IDs, actionable rules, referenced
blueprints, and representative positive and negative tests. Do not repeat aiscb
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

Keep pack counts and trigger descriptions small. Generate discovery metadata
from the catalog; catalog summaries do not replace packs.

## 3. Store approved values in blueprints

Blueprints contain approved values, not behavior: for example claim names,
group mappings, cookie attributes, headers, libraries, limits, error shapes,
and permitted log fields. The overlay or pack says when a value is required.

Version each blueprint and validate it with a strict schema. Reject unknown or
duplicate fields, invalid types or values, and incompatible versions. Load only
the verified bundle copy; keep source URLs as provenance metadata, not policy.

Maintain blueprints through reviewed Git changes. If another system is
authoritative, constrain imports to its allow-listed HTTPS endpoint, reject
off-host redirects, and validate bounded downloads before opening a pull
request. Failures leave the approved copy untouched. Review changes to
authentication, authorization, transport, secrets, or limits as policy changes;
allow a faster path only for compatible, non-security-sensitive values.

## 4. Generate adapters for each tool

Generate adapters from reviewed bundle sources; do not edit them by hand. In a
combined file, place aiscb before the overlay and remove its import marker.

Initially load only aiscb, the overlay, and discovery metadata. Load packs on
matching semantic or path triggers. Prefer native skills for semantic triggers
and path-scoped instructions for directory or file-pattern matches.

| Tool | On-demand packs | Path-specific option |
| --- | --- | --- |
| Claude Code | `.claude/skills/<pack>/SKILL.md` | `.claude/rules/*.md` with `paths` |
| Codex | `.agents/skills/<pack>/SKILL.md` | Nested `AGENTS.md` when directory scope fits |
| Copilot | `.github/skills/` or `.agents/skills/` | `.github/instructions/*.instructions.md` with `applyTo` |

If a surface cannot load skills, generate a compact route with the domain,
trigger, and verified pack path. If it cannot load packs on demand, include the
applicable packs in its adapter. Test deferred loading.

Set size and token budgets for initial content, discovery metadata, and packs.
Fail generation on unexpected growth or repeated requirements.

Tool-specific points:

- **Claude Code:** use managed-policy `CLAUDE.md` or another root-managed,
  immutable path for organization-wide enforcement. Imports load eagerly;
  skills load on demand.
- **Codex:** generate an `AGENTS.md` containing aiscb followed by the overlay;
  Codex has no documented import directive for this file. Keep it within the
  configured instruction limit and install packs as skills. Codex discovers its
  `AGENTS.md` chain once per run.
- **GitHub Copilot:** because import support varies by surface, use relative
  imports only where verified; otherwise generate combined instructions.

Relevant documentation: [Claude Code instructions](https://code.claude.com/docs/en/memory)
and [skills](https://code.claude.com/docs/en/slash-commands),
[Codex `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md/) and
[skills](https://developers.openai.com/codex/skills/), and the GitHub Copilot
[custom-instructions support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

Record adapter digests in the manifest. Do not overwrite local changes without
confirmation and backup. Validate source files before generation, then verify
the generated adapter against its digest.

## 5. Release and distribute the bundle

Publish each approved bundle under an immutable version. Its manifest records:

- bundle, overlay, and aiscb IDs, plus the exact upstream digest;
- catalog, pack, blueprint, schema, and compatibility versions and digests;
- every installed path, file size, and SHA-256 digest;
- adapter-generator version and measured instruction budgets; and
- release provenance or package-signature reference.

A protected or moving branch is not an immutable release. Prefer signed
packages or device management for developer machines, pinned bot updates for
repositories, and a manually verified installer only as a fallback.

Roll out to a small group first and keep rollback to one managed version change.
Use package or device management for inventory; an assistant response does not
prove fleet state.

## 6. Update before starting the assistant

Apply updates through package management, a launcher, or a scheduled device
task before the assistant starts. Do not update instruction files from a
session-start hook: tools may already have loaded the previous version while a
helper reports the new disk version.

If offline, retain the last verified bundle and apply the staleness policy.
Track the last attempt separately from the last successful update. A startup
hook may report the installed version, but not claim that the model loaded it.

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

If the fork keeps the upstream release check, preserve its URL, redirect, and
destination validation. Ship reviewed helper sources rather than editing
installed copies.

Automate checks for catalog consistency, valid aiscb mappings, unique IDs,
complete routes, blueprint schemas and compatibility, safe paths, replaced
placeholders, adapter order and budgets, manifest digests, and atomic install.
Test install, update, rollback, interruption, drift, and missing or incompatible
content on each supported operating system.

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
