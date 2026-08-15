# Load the baseline for repository agents

## Problem

`CLAUDE.md` imports both the repository instructions and the secure-coding
baseline, but tools that load only `AGENTS.md` receive a request to read the
baseline instead of the baseline itself. The specification-driven workflow is
also described only as "the workflow" in the root instructions.

## Goal

Give every tool that loads the root `AGENTS.md` the repository workflow and the
complete secure-coding baseline, name specification-driven development
explicitly, and prevent the embedded baseline from drifting from its normative
source.

## Non-goals

Do not change the baseline's normative behavior, move its source file, or add a
new model-test obligation.

## Compatibility

`AGENTS.md` becomes larger because it carries the baseline verbatim. Claude
Code continues to receive both instruction sets through one import instead of
loading the baseline twice.
