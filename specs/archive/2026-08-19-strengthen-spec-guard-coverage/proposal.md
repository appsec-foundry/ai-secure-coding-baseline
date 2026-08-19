# Strengthen spec guard coverage

## Problem

The command hook is not loaded when Claude Code starts below the repository
root, and command-hook startup failures or timeouts produce no decision. The
guard also misses several ordinary shell, PowerShell, and MCP mutations whose
inputs visibly target `specs/`.

## Goal

Add a native ask rule for built-in file edits, cover the reproduced mutation
forms, and state the root-start and fail-open boundaries accurately. Preserve
the existing Python guard as defense in depth for shell, PowerShell, and MCP
calls.

## Non-goals

Do not claim complete shell-effect inference, add a shell parser or dependency,
or make the guard a substitute for Claude Code permissions and sandboxing.
Keep conservative prompts such as copying a spec outward unchanged.

## Compatibility

Direct edits under project-root `specs/` encounter a native ask rule as well as
the existing hook decision. The newly recognized mutation forms ask instead of
falling through. Users relying on the tracked project hook must launch Claude
Code from the repository root.
