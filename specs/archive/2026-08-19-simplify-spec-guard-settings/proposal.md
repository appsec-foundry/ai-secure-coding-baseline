# Simplify the spec guard settings

## Problem

The spec guard is registered through two `PreToolUse` matcher groups only to
avoid starting the guard for `Write` calls outside `specs/`. The split makes
the small project setting harder to understand and maintain.

## Goal

Register every covered tool in one unfiltered matcher group and let
`scripts/spec_guard.py` remain the single place that decides whether a call
identifies a write under this repository's `specs/` directory.

## Non-goals

Do not change the native edit permission rule, the covered tool set, the guard's
allow, ask, or block decisions, or the normative secure-coding baseline.

## Compatibility

Approval behavior remains unchanged. The guard process now also starts for
direct `Write` calls outside `specs/`, restoring a small amount of process
overhead in exchange for a simpler registration.
