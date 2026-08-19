# Remove the duplicate spec guard settings snippet

## Problem

`scripts/spec-guard.settings.json` duplicates the active project hook from
`.claude/settings.json`. It is not loaded at runtime, and maintaining the same
configuration in two files adds synchronization work without a current
consumer.

## Goal

Make `.claude/settings.json` the single maintained Claude Code hook
configuration, remove the unused snippet, and keep registration and guard
behavior covered by the existing deterministic test.

## Non-goals

Do not change the hook matchers, path filter, guard decisions, or the normative
secure-coding baseline. Do not rewrite archived change records that accurately
describe the repository at the time they were completed.

## Compatibility

Claude Code behavior in this repository is unchanged because it already loads
`.claude/settings.json`. Consumers that manually copied the standalone snippet
must instead copy the hook from the project settings file.
