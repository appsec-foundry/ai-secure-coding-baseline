# Requirements

## SPEC-GUARD-001 Load the project hook

Source: the user's explicit request in this conversation to verify and fix the
spec guard, and the existing installation instruction in `AGENTS.md`.

The repository must register `scripts/spec_guard.py` as a Claude Code
`PreToolUse` command hook in tracked project settings.

Acceptance: `.claude/settings.json` contains the registration in the current
Claude Code schema, and an automated check fails when the registration is
missing or no longer matches the maintained hook snippet.

## SPEC-GUARD-002 Ask on identifiable spec writes

Source: the user's approval in this conversation of the proposed coverage and
the existing explicit-approval rule in `AGENTS.md`.

The hook must ask before native file writes into this repository's `specs/`
directory and before shell, PowerShell, or recognizably mutating MCP calls whose
input identifies such a target. Path resolution must account for the hook
working directory and the Claude project-root variable.

Acceptance: end-to-end payload tests cover native writes, ordinary redirects,
the hook working directory, project-root variables, `dd`, PowerShell, and a
representative MCP filesystem write, while reads and writes elsewhere remain
unprompted.

## SPEC-GUARD-003 Fail closed on invalid matched input

Source: the user's approval in this conversation of fail-closed handling and
the existing requirement in `AGENTS.md` that spec writes need explicit
approval.

A matched mutation-capable hook call with malformed or structurally invalid
input must be blocked rather than silently allowed.

Acceptance: subprocess tests show invalid JSON and missing required tool input
exit with Claude Code's blocking status and a diagnostic on stderr.

## SPEC-GUARD-004 State the enforcement boundary

Source: the user's approval in this conversation of the proposed limitation
and the existing best-effort caveat in `scripts/spec_guard.py`.

Repository documentation must distinguish the writes the hook can identify
from effects hidden inside arbitrary programs or scripts and must not describe
the hook as complete enforcement.

Acceptance: the guard documentation names the opaque-program limitation and
the workflow documentation describes the hook as a tested project guard with
that boundary.
