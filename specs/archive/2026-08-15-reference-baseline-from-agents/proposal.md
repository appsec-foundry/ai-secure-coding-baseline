# Reference the baseline from agent instructions

## Problem

The root `AGENTS.md` contains a generated copy of the complete secure-coding
baseline. That makes the repository instructions look like the normative
requirements source even though the baseline and its requirements catalog are
maintained separately.

## Goal

Keep `AGENTS.md` focused on the repository workflow, require agents to read the
normative baseline through a reference, and keep requirements and change
specifications under `specs/`.

## Non-goals

Do not change any secure-coding rule or the model-test installation mechanism.

## Compatibility

Agents must follow the reference to load the baseline instead of receiving its
full text in `AGENTS.md`. This is intentionally less automatic for agents that
load `AGENTS.md` but do not resolve referenced files.
