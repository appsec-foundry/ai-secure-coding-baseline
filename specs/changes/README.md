# Change templates

Copy these three files into `changes/<short-name>/`. Keep them short; they are
a working record, not a deliverable. `../README.md` explains the workflow.

## `proposal.md`

```markdown
# <Title>

## Problem

## Goal

## Non-goals

## Compatibility
```

## `requirements.md`

One entry per behavior the baseline must have. Give it an ID, name its source,
state the behavior plainly, and say what observable result accepts it. Add an
example only when it helps.

```markdown
# Requirements

## <ID> <Short name>

Source: <the request, the document, or the commit>

<What an assistant must do, in a sentence or two.>

Acceptance: <the observable result that shows the requirement is met>

Example: <a situation and the expected behavior.>
```

## `tasks.md`

```markdown
# Tasks

- [ ] Change the baseline.
- [ ] Update the test cases and their requirement IDs.
- [ ] Update `specs/requirements.md` and the documentation.
- [ ] Run `make check`.
- [ ] Run the affected model cases, or note why not.
- [ ] Archive this directory.
```
