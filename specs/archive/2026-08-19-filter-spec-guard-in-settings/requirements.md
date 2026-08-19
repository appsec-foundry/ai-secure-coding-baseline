# Requirements

## SPEC-GUARD-FILTER-001 Pre-filter direct writes

Source: the user's explicit request in this conversation to implement the
`Write` hook with a settings-level path filter for better performance.

The tracked Claude Code hook settings must use a project-root-relative `if`
filter so the command hook starts for `Write` only when its target is under
`specs/`.

Acceptance: both maintained settings files register `Write` separately with
`if: Write(/specs/**)`, and the automated registration check rejects a missing,
working-directory-relative, or otherwise changed filter.

## SPEC-GUARD-FILTER-002 Preserve remaining guard coverage

Source: the user's approval of the proposed change in this conversation and
the existing explicit-approval rule in `AGENTS.md`.

The optimization must leave `Edit`, `MultiEdit`, `NotebookEdit`, `Bash`,
`PowerShell`, and MCP calls on the existing unfiltered command hook, and the
Python guard must remain the authority that decides whether a matched target
is inside this repository's `specs/` directory.

Acceptance: the settings registration check requires the unfiltered fallback
matcher and the existing allow, ask, and block payload tests continue to pass.
