# Sourced constraints

This process change introduces no new secure-coding behavior. Its constraints
come from existing repository sources rather than newly designed product
requirements.

## Preserve the normative artifact

Source: `README.md` describes `secure-coding-baseline.md` as the complete rules,
the source of truth for copied instruction files, and a deliberately compact
artifact.

- Keep `secure-coding-baseline.md` as the single normative, distributable file.
- Add identifiers only; do not rewrite its rule behavior as part of this change.
- Do not duplicate its normative prose in the specification directory.

## Preserve documented test relationships

Source: the `covers` arrays in `tests/cases/*/checks.json` at `HEAD`, introduced
by commits `51c7cb4`, `a24624e`, and `5822b48`.

- Replace each free-form coverage name with the stable ID of the same existing
  baseline group.
- Do not add a relationship that was not present in the corresponding `covers`
  array.
- Make `make check` reject unknown and duplicate requirement references.

## Preserve the evaluation model

Source: `tests/README.md` and the comments in `Makefile` distinguish the free,
deterministic suite validation from costly, stochastic model runs.

- Keep `make check` free of model calls.
- Keep A/B model runs as evidence rather than making them a new hard gate.

## Record provenance without reconstructing intent

Source: current baseline text and `git blame HEAD` for that file.

- Index the existing top-level behavior groups and the commits that currently
  contribute their text.
- Describe the commit list as text provenance, not as a complete rationale.
- Do not infer additional requirements, exemptions, or test obligations from
  an absence in the history.
