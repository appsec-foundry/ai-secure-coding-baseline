# Use Semantic Versioning for the baseline ID

## Problem

The current `aisec-0.1` identifier names a release line but cannot distinguish
successive normative revisions within that line.

## Goal

Give every normative baseline revision a Semantic Versioning identifier, start
the current baseline at `aisec-0.1.0`, and keep the documented identifier in
sync with the normative file.

## Non-goals

Do not add a content digest, change any secure-coding rule, or introduce a
release automation workflow.

## Compatibility

Consumers and derived baselines using `aisec-0.1` must update their identifier
to the three-part form, such as `aisec-0.1.0` or `aisec-0.1.0+acme`.
