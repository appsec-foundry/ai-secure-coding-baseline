# Requirements

## SPEC-GUARD-SNIPPET-001 Keep one settings source

Source: the user's explicit request in this conversation to delete the
redundant `scripts/spec-guard.settings.json` file.

The repository must keep `.claude/settings.json` as the only maintained Claude
Code registration for `scripts/spec_guard.py` and must not advertise a separate
settings snippet for merging elsewhere.

Acceptance: `scripts/spec-guard.settings.json` is absent, and current
documentation names only `.claude/settings.json` as the project registration.

## SPEC-GUARD-SNIPPET-002 Preserve direct registration checks

Source: the user's approval of this change and the existing registration
contract in `specs/README.md`.

The deterministic guard test must continue to validate the active project
settings directly, including the filtered `Write` group and the unfiltered
fallback group, without comparing them to a duplicate file.

Acceptance: the registration test reads `.claude/settings.json` as its sole
settings input, and all existing allow, ask, and block payload cases pass.
