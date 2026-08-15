# Requirements

## AGENT-LOAD-002 Reference the normative baseline

Source: the user's explicit request in this conversation to include the
baseline by reference and keep requirements under `specs/`.

`AGENTS.md` must identify `secure-coding-baseline.md` as the normative baseline
and explicitly require an agent to read and follow it before doing repository
work. It must not contain a generated copy of the baseline.

Acceptance: `AGENTS.md` contains the required reference, contains no generated
baseline block, and `make check` validates that reference.

## AGENT-SPECS-001 Keep requirements under specs

Source: the user's explicit request in this conversation to include the
baseline by reference and keep requirements under `specs/`.

Behavioral change requirements and the readable requirements catalog must
remain under `specs/`; `AGENTS.md` may describe how to use them but must not
duplicate them.

Acceptance: this change is specified under `specs/changes/`, the catalog stays
at `specs/requirements.md`, and the repository documentation describes those
roles accurately.

## AGENT-SYNC-002 Remove obsolete generated-copy machinery

Source: AGENT-LOAD-002 in this change and the existing repository documentation
that generated synchronization exists only for the embedded baseline copy.

The repository must remove synchronization commands and checks whose sole
purpose is maintaining the former generated copy, while retaining a
deterministic check that `AGENTS.md` references the normative baseline.

Acceptance: the obsolete sync command is absent and representative self-check
tests fail when the required reference is missing or the generated block is
reintroduced.

## AGENT-CLAUDE-002 Import the referenced baseline for Claude

Source: AGENT-LOAD-002 in this change and the existing `README.md` description
of Claude Code's native import mechanism.

`CLAUDE.md` must import both the repository instructions and the normative
baseline so replacing the generated copy with a reference does not remove the
baseline from Claude Code's initial context.

Acceptance: `CLAUDE.md` imports `AGENTS.md` and `secure-coding-baseline.md`
exactly once each.
