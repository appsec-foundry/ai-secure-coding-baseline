# Activate and strengthen the spec guard

## Problem

The repository carries a valid Claude Code `PreToolUse` hook snippet, but no
project settings file loads it, so the guard is inactive. Its tests invoke the
Python script directly and therefore pass without detecting that installation
gap. The script also misses representative writes through the hook working
directory, project-root variables, additional shell tools, PowerShell, and MCP
file tools, and malformed hook input fails open.

## Goal

Load the guard from project settings, cover the concrete bypasses verified in
this change, fail closed when a matched hook call cannot be interpreted, and
test both registration and behavior. Keep the documented guarantee no broader
than the hook can establish.

## Non-goals

Do not claim to infer the filesystem effects of arbitrary opaque programs or
scripts from a shell command. Do not change the normative secure-coding
baseline or add ports for tools other than Claude Code.

## Compatibility

Reads remain unprompted. More mutation-capable calls that can be tied to this
repository's `specs/` directory ask for approval. Claude Code loads the tracked
project hook after applying its workspace-trust rules.
