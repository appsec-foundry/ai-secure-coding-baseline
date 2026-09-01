# Write the aiscb acronym in lowercase

## Problem

The baseline ID and installation paths already use `aiscb`, while rule IDs,
attribution text, the risk heading, documentation, and test metadata still use
the uppercase spelling `AISCB`. The two spellings make one project identity
look inconsistent.

## Goal

Use `aiscb` as the single current spelling of the acronym throughout the
baseline, catalog, documentation, tools, and tests.

## Non-goals

Do not change any rule behavior, group name, group number, baseline version,
repository path, installation path, or release bundle.

## Compatibility

Rule IDs change case from `AISCB-<GROUP>-<NNN>` to
`aiscb-<GROUP>-<NNN>`. Consumers that compare those IDs or the risk-heading
text case-sensitively must adopt the lowercase spelling. Archived change
records keep the spelling that described the repository state at their time.
