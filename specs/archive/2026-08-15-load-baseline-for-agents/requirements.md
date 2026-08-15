# Requirements

## AGENT-SDD-001 Name specification-driven development

Source: the user's request on 2026-08-15 to add the missing reference to
spec-driven development, and commit `279d7b4`, which introduced that workflow.

The root agent instructions must explicitly name specification-driven
development and direct maintainers to its authoritative workflow.

Acceptance: `AGENTS.md` names specification-driven development and points to
`specs/README.md`.

## AGENT-LOAD-001 Load the baseline through AGENTS.md

Source: the user's 2026-08-15 request and approval to fix the baseline being
included only by `CLAUDE.md`, plus `README.md` under "Every other agent", which
says an existing `AGENTS.md` must append the baseline because the format has no
import directive.

`AGENTS.md` must contain the complete text of `secure-coding-baseline.md` so
agents that load only the shared instruction file receive the baseline without
an optional follow-up read.

Acceptance: the generated baseline block in `AGENTS.md` is byte-for-byte equal
to the normative baseline after normalizing only the final newline.

## AGENT-SYNC-001 Reject baseline drift

Source: `README.md` under "Keeping the copies in sync", which requires generated
instruction copies, and the user's 2026-08-15 approval to implement the
proposed deterministic drift check.

The repository must provide a repeatable command that refreshes the generated
baseline block and `make check` must fail when that block differs from the
normative baseline.

Acceptance: the sync command restores an altered generated block, and the
deterministic self-check reports an altered or missing block.

## AGENT-CLAUDE-001 Avoid duplicate Claude instructions

Source: the user's 2026-08-15 approval of the proposed structure in which
`CLAUDE.md` imports only the combined `AGENTS.md`.

`CLAUDE.md` must import the combined `AGENTS.md` without separately importing
the baseline a second time.

Acceptance: `CLAUDE.md` contains one import, `@AGENTS.md`.
