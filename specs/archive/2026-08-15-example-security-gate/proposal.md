# Add an example deterministic gate

## Problem

The README states that this baseline guides an LLM and is not an enforceable
control, and that a specification without evidence is guidance rather than a
control. Both statements are correct and neither is illustrated. A reader who
accepts them has no starting point for the deterministic half, and no way to see
which rule groups can be checked outside a model and which cannot.

## Goal

Ship one small, tested example of a check that runs outside the model: a Claude
Code `PreToolUse` hook that denies a short list of patterns and names the rule
group behind each denial. Make the boundary explicit — what a pattern gate can
decide, what needs context and therefore asks instead of blocking, and what no
gate can see.

## Non-goals

- Making the baseline enforceable, or implying that a gate does.
- A second product: no policy format, no per-tool matrix, no coverage claim over
  the rule groups.
- Ports to tools without a hook API. Copilot and Codex have none.
- The warn tier. Everything needing context is named in the example's README and
  left unimplemented.
- Changing `secure-coding-baseline.md`. No rule text moves.

## Compatibility

The baseline is unchanged, so assistant behavior is unchanged. `make check` gains
one test script, which runs in the same second and calls no model. Nothing in
`specs/` or `tests/cases/` depends on the example, and deleting the directory
leaves the suite passing.
