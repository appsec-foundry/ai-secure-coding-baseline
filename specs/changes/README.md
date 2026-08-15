# Active changes

Create one directory per substantive change with the following files.

## `proposal.md`

```markdown
# <Change title>

## Problem

## Goal

## Non-goals

## Compatibility
```

## `requirements.md`

Derive requirements from the approved request, existing documentation, or
commit history and name the source. If the sources are ambiguous, ask before
adding a requirement. Use `MUST`, `MUST NOT`, `SHOULD`, and `MAY` deliberately.
Give each requirement at least one observable scenario supported by its source.

```markdown
# Requirements

## <CHANGE-ID-001> <Behavior>

Source: <request, document, or commit>

The baseline MUST ...

### Scenario: <name>

- Given ...
- When ...
- Then ...
```

## `tasks.md`

```markdown
# Tasks

- [ ] Update the normative baseline.
- [ ] Add or update model cases and requirement references.
- [ ] Update the requirement index and documentation where applicable.
- [ ] Run `make check`.
- [ ] Run relevant A/B tests or record why they are deferred.
- [ ] Archive this change when complete.
```
