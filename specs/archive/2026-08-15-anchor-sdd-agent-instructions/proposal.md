# Anchor specification-driven development in agent instructions

## Problem

The SDD workflow is documented under `specs/`, but no repository instruction
file requires coding agents to read or follow it. An agent can therefore begin
changing the baseline without applying the sourcing and approval boundary.

## Goal

Make the repository-wide agent instructions require the existing SDD workflow,
prohibit unsourced normative decisions, and expose the same instructions to
Codex and Claude Code.

## Non-goals

- Adding or changing any secure-coding requirement.
- Adding test obligations, exemptions, or coverage relationships.
- Duplicating the baseline or specification documents in agent instructions.
- Preventing agents from documenting or implementing explicitly approved work.

## Compatibility

The new files affect repository maintenance sessions only. The published
baseline remains the single normative product specification and its content is
unchanged by this change.
