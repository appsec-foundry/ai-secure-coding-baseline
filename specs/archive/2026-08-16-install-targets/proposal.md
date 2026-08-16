# Install targets for coding agents

## Problem

Installing the baseline means putting it where a tool already looks, and every
tool looks somewhere else. `README.md` explains those locations in prose, so
each user repeats the same symlink work by hand and gets it subtly wrong — a
copy instead of a link, the wrong directory, an `AGENTS.md` silently
overwritten.

## Goal

Make the documented installation executable: one target per tool that links
`secure-coding-baseline.md` into that tool's instruction location, for the
current project or for the machine.

## Non-goals

Do not change any secure-coding rule. Do not embed or generate a copy of the
baseline anywhere in this repository. Do not install anything automatically as
a side effect of another target.

## Compatibility

New files and targets only; nothing existing changes behavior. Tools are table
entries, so a tool whose location is not yet established — Grok among them —
becomes one row once its path is confirmed against current documentation.
