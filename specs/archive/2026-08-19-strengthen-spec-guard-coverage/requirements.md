# Requirements

## SPEC-GUARD-COVERAGE-001 Add native edit prompting

Source: the user's explicit request in this conversation to implement the
review recommendation, and Claude Code's documented project-root permission
rule syntax.

Project settings must carry a native ask rule for built-in edits under the
repository-root `specs/` directory so those edits do not rely only on the
Python command hook.

Acceptance: `.claude/settings.json` contains `Edit(/specs/**)` in
`permissions.ask`, and the registration test fails when that rule is absent.

## SPEC-GUARD-COVERAGE-002 Cover reproduced mutations

Source: the user's approval of the review recommendation and the concrete
misses reproduced during that review.

The guard must ask when `curl -o`, `tar -x`, `find -delete`, `chmod`, `git
clone`, PowerShell `Invoke-WebRequest -OutFile`, or an MCP `append_file` call
visibly targets this repository's `specs/` directory.

Acceptance: end-to-end payload tests exercise each named form and receive
`permissionDecision: ask`; existing allow and block cases continue to pass.

## SPEC-GUARD-COVERAGE-003 State runtime boundaries

Source: the user's approval of the review recommendation and the current
Claude Code documentation for project settings and command-hook failures.

Current repository guidance must say that the tracked project hook requires
launching Claude Code from the repository root and that a command hook which
cannot start or times out produces no decision. It must retain the existing
opaque-program limitation.

Acceptance: `AGENTS.md`, `README.md`, the workflow documentation, and the guard
module describe the applicable boundary without claiming hard enforcement.
