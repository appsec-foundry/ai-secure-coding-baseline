# Coordinate minor and major version levels

## Problem

The current policy infers minor and major baseline versions automatically from
the kind of normative change. That turns a release-level decision into an
automatic side effect of editing the baseline.

## Goal

Increment the patch component by default for every normative revision. Use a
minor or major version only after that level was explicitly agreed.

## Non-goals

Do not change the three-component identifier format, automate releases, or
change any secure-coding rule.

## Compatibility

This policy supersedes `BASELINE-VERSION-002` from the archived SemVer change.
The pending risk-reporting revision becomes `aisec-0.1.1` instead of
`aisec-0.2.0`. Consumers must use the identifier of the published text rather
than infer a version level from its contents.
