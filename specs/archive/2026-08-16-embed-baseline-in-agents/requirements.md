# Requirements

## AGENT-LOAD-003 Carry the baseline in agent instructions

Source: the user's explicit request in this conversation to include the baseline
directly in `AGENTS.md` so that agents which do not resolve references still
receive it.

`AGENTS.md` must contain the repository workflow instructions followed by the
complete normative baseline text, marked as generated from
`secure-coding-baseline.md`.

Acceptance: `AGENTS.md` ends with a generated block whose content equals
`secure-coding-baseline.md`, and `make check` fails when it does not.

Example: an assistant that loads only `AGENTS.md` and resolves no references
answers `baseline?` with `aisec-0.1`.

## AGENT-SYNC-003 Generate the copy and reject drift

Source: AGENT-LOAD-003 in this change, and `README.md`, which requires copied
instruction files to be generated from the one normative source rather than
edited by hand.

The repository must provide a command that rewrites the block in `AGENTS.md`
from `secure-coding-baseline.md`, and `make check` must fail when the two differ.

Acceptance: `make sync-agents` updates the block, and the self-check reports a
difference between the block and the normative file.

## AGENT-CLAUDE-003 Import agent instructions once for Claude

Source: the user's explicit request in this conversation for a single import
point, together with `README.md`, which records that Claude Code does not load
`AGENTS.md` on its own.

`CLAUDE.md` must import `AGENTS.md` and must not import the baseline a second
time, because `AGENTS.md` already carries it.

Acceptance: `CLAUDE.md` imports `AGENTS.md` exactly once and imports
`secure-coding-baseline.md` not at all; `make check` enforces both.
