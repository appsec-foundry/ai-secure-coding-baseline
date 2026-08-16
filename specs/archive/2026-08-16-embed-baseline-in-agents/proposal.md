# Embed the baseline in agent instructions

## Problem

`AGENTS.md` only references `secure-coding-baseline.md`. `AGENTS.md` has no
import directive, so every assistant except Claude Code reads the reference as
prose and has to decide to open the file. On a prompt that does not mention
security, it does not. Working on this repository with Codex therefore happens
without the baseline in context — the failure the baseline exists to prevent.

## Goal

Put the normative baseline text into `AGENTS.md` so every tool that reads that
file loads the rules, and keep it a generated copy that cannot drift from
`secure-coding-baseline.md`.

## Non-goals

Do not change any secure-coding rule. Do not add per-tool configuration or
machine-local installation to the repository.

## Compatibility

This reverses `AGENT-LOAD-002` from
`archive/2026-08-15-reference-baseline-from-agents/`, which replaced the
generated copy with a reference. The concern behind that change — `AGENTS.md`
reading as the normative source — is met by the generated block being marked as
generated and verified by `make check`, not by leaving the text out.

`CLAUDE.md` no longer imports the baseline separately; `AGENTS.md` carries it.
Anyone editing `AGENTS.md` by hand inside the block loses the edit on the next
`make sync-agents`.
