# Adapting aiscb inside an organization

aiscb states rules that hold anywhere. An organization has more of them: the
approved identity provider, the claim that carries the tenant, the libraries
that passed review, the headers every service must send. This guide shows one
way to add those rules beside the baseline instead of editing it, and how to get
the result onto developer machines.

The examples use Acme names — replace them. This is a recommendation, not part
of the baseline.

## The parts

| Part | Content |
| --- | --- |
| aiscb baseline | upstream rules, unchanged, pinned to an approved release |
| Overlay | the few organization rules that always apply |
| Requirement packs | rules and acceptance criteria for one domain, loaded only for matching work |
| Blueprints | approved values: libraries, claim names, limits, headers, mappings |
| Adapters | the generated files each assistant actually reads |

The split exists because context is expensive. Whatever sits in the overlay is
present for every task, so only invariants belong there. The twenty detailed
rules about authentication belong in an authentication pack that is read when
someone touches authentication.

A value belongs in a blueprint when the rule still reads correctly without it.
"Accept only approved group IDs" is the rule; the list of group IDs is the
blueprint. Keeping them apart means a new group does not require a policy
change.

Say explicitly where an organization rule narrows a named aiscb rule. Where it
stands alone, give it an ID of its own rather than inventing an aiscb target it
does not have. An overlay may narrow aiscb, never relax it.

## The overlay

Give the overlay its own ID, such as `acme-sec-1.0.0`. aiscb keeps its ID and
its file; do not copy its rules into the overlay.

Keep it short. It carries the security-critical invariants, requires the
matching packs and blueprints to be loaded before affected work, and stops that
work when required content is missing, invalid, or contradictory. Bundle paths
are placeholders that the build replaces with verified absolute paths.

```markdown
@<bundle-dir>/secure-coding-baseline.md

# Acme Secure Coding Overlay

`baseline-id: acme-sec-1.0.0`. Extends aiscb (`aiscb-0.1.11`). On `baseline?`,
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

Work that needs no pack keeps running.

## Requirement packs and routing

One pack per domain: authentication, tenant isolation, browser security, APIs.
Rationale and history stay in the policy system. A pack carries stable
requirement IDs, actionable rules, the blueprints it references, and
representative positive and negative tests. It does not repeat aiscb text.

A catalog lists every pack with its ID, file, owner, source, a short trigger
description, and any path triggers. It also records how each requirement maps to
aiscb — `narrows` with the named rules, or `organization` for a standalone one.
The discovery metadata the assistant sees first is generated from that catalog,
so trigger descriptions have to stay short. Validate the catalog: duplicate IDs,
unknown aiscb targets, contradictory routes, and packs that no catalog entry
mentions otherwise fail silently.

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

Several packs may match one task. A catalog summary is a pointer to a pack, not
a replacement for it.

## Blueprints

Blueprints hold approved values, not behavior: claim names, group mappings,
cookie attributes, headers, libraries, limits, error shapes, permitted log
fields. The overlay or the pack says when a value is required.

Version each blueprint and validate it against a strict schema that rejects
unknown fields and incompatible versions. The assistant loads the verified copy
from the bundle; a source URL is provenance, not policy.

Change blueprints through reviewed Git changes. If another system is
authoritative, import from it into a pull request rather than at load time:
fetch from an allow-listed endpoint without following off-host redirects, and
validate the bounded download before it reaches the repository. A failed import
leaves the approved copy untouched. Values that touch
authentication, authorization, transport, secrets, or limits are policy changes
and get a policy review; a faster path is reasonable for the rest.

## Adapters per tool

Adapters are generated from the reviewed bundle, never edited by hand. Where a
tool needs one combined file, aiscb goes first, the overlay second, and the
import marker is removed.

Load aiscb, the overlay, and the discovery metadata at start. Everything else
waits for a trigger — a semantic one through a skill, or a path match where the
domain follows the directory layout.

| Tool | On-demand packs | Path-specific option |
| --- | --- | --- |
| Claude Code | `.claude/skills/<pack>/SKILL.md` | `.claude/rules/*.md` with `paths` |
| Codex | `.agents/skills/<pack>/SKILL.md` | Nested `AGENTS.md` when directory scope fits |
| Copilot | `.github/skills/` or `.agents/skills/` | `.github/instructions/*.instructions.md` with `applyTo` |

Claude Code loads imports eagerly and skills on demand; for organization-wide
enforcement, place the file at a managed, root-owned path. Codex has no
documented import directive for `AGENTS.md`, so generate the combined file,
stay inside the configured instruction limit, and install packs as skills. Codex
reads its `AGENTS.md` chain once per run. Copilot import support differs per
surface, so use relative imports only where you verified them and generate
combined instructions elsewhere.

Documentation: [Claude Code instructions](https://code.claude.com/docs/en/memory)
and [skills](https://code.claude.com/docs/en/slash-commands),
[Codex `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md/) and
[skills](https://developers.openai.com/codex/skills/), and the GitHub Copilot
[custom-instructions support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

Where a surface cannot load packs on demand, put the applicable packs in its
adapter and accept the size. Set budgets for the always-loaded content and fail
generation when it grows unexpectedly, because nobody notices context creep by
reading a diff.

## Releasing the bundle

Name owners for upstream updates, organization requirements, and tool support
before the first release; each of the three is a separate job.

A release is one immutable version containing the unchanged aiscb file, the
overlay, catalog and packs, blueprints, the generated adapters, and a manifest.
The manifest pins the bundle, overlay, and aiscb IDs including the upstream
digest, and records every installed path with its size and SHA-256. A protected
branch is not a release.

Install releases side by side and switch atomically:

```text
~/.local/share/aiscb/
├── releases/acme-sec-0.9.0/
├── releases/acme-sec-1.0.0/
└── current -> releases/acme-sec-1.0.0/
```

Verify the bundle before moving `current`, and keep the previous release so
rollback is one change. Generated paths point at the versioned directory, not at
`current`, so a running session cannot end up reading two releases at once.

Prefer signed packages or device management for developer machines and pinned
bot updates for repositories; a manually verified installer is the fallback.
Roll out to a small group first. Inventory comes from package or device
management — an assistant's answer about its own version proves nothing about
the fleet.

Apply updates before the assistant starts, through package management, a
launcher, or a scheduled task. A session-start hook is the wrong place: the tool
may already have loaded the old file while the hook reports the new one on disk.
When a machine is offline, keep the last verified bundle and let the staleness
policy decide; track the last attempt separately from the last success.

The upstream installer manages a single baseline file, so a bundle needs its
own. What matters is that it authenticates the manifest and verifies every file
before executing anything, installs into a new versioned directory and switches
in one step, records what it placed so drift detection and uninstall work, and
leaves unrelated files alone. Test install, update, rollback, and an interrupted
install on every operating system you support.

## Verifying

Four questions, each needing different evidence, before promotion and after
changes to the overlay, catalog, packs, blueprints, generator, installer, or
supported tool versions:

1. **Is it installed?** Manifest, active release, and destination digests match.
2. **Is it loaded?** Check the tool's own diagnostics, and start a fresh Codex
   run after an update. `baseline?` works as a cross-tool smoke test: the answer
   should name both IDs and their files.
3. **Is the right pack selected?** The expected pack loads on its trigger,
   unrelated tasks do not pull it in, and a missing required pack stops only the
   affected work.
4. **Does behavior follow?** Run positive and negative cases for SSO, claims,
   tenant isolation, browser policy, limits, and missing or invalid content.

The first three are cheap and prove less than they look like. A correct
`baseline?` answer shows the assistant can see the instructions, not that it
follows them, and a file being visible says nothing about whether a pack was
actually selected.

## Limits

An overlay changes what an assistant is told. It cannot guarantee that the
assistant complies or that every machine is current. Every property that must
hold still needs application authorization, tests, CI gates, deployment policy,
and runtime controls behind it.
