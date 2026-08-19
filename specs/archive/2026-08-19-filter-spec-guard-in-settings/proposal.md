# Filter direct spec writes before starting the guard

## Problem

The project hook starts `scripts/spec_guard.py` for every `Write` call, even
when the target is clearly outside `specs/`. Claude Code can apply a path-aware
`if` filter before spawning the command hook.

## Goal

Avoid starting the Python guard for direct `Write` calls outside this
repository's `specs/` directory without reducing the existing protection for
spec writes or other mutation-capable tools.

## Non-goals

Do not move the authoritative path decision out of `spec_guard.py`, narrow the
protected area to one spec file, or pre-filter shell, PowerShell, MCP, or other
file-editing tools whose inputs still require the existing guard logic.

## Compatibility

Direct `Write` calls under project-root `specs/` still ask for approval. Other
`Write` calls skip the guard process, while all previously matched non-`Write`
tools continue through it unchanged. The `if` field requires a Claude Code
version that supports permission-rule filters on hook handlers.
