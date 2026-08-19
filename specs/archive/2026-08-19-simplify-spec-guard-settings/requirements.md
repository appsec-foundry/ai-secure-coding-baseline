# Requirements

## SPEC-GUARD-SETTINGS-001 Use one matcher group

Source: the user's explicit request in this conversation to replace the split
hook registration with one matcher block.

The tracked Claude Code settings must register `Write`, `Edit`, `MultiEdit`,
`NotebookEdit`, `Bash`, `PowerShell`, and MCP tools in one unfiltered
`PreToolUse` matcher group.

Acceptance: `.claude/settings.json` contains exactly one spec guard matcher
group, its matcher contains the complete maintained tool set, and its handler
has no `if` filter.

## SPEC-GUARD-SETTINGS-002 Preserve guard behavior

Source: the user's approval of the proposed simplification and the existing
explicit-approval rule in `AGENTS.md`.

The simplification must retain the native edit ask rule and must not change the
guard's decisions for identifiable spec writes, unrelated calls, or malformed
matched input.

Acceptance: the registration test requires the native ask rule and single hook
group, and all existing ask, allow, and block payload cases pass.
