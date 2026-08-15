# Specification-driven changes

`secure-coding-baseline.md` is the normative product specification and remains
the single file distributed to coding assistants. The files here index the
requirements already present in that document and describe changes to them;
they do not add or duplicate rule text.

## Requirement IDs

Each top-level behavior group in the baseline has a stable ID of the form
`AISEC-<AREA>-<NNN>`. An ID identifies behavior, not a heading or line number,
and remains unchanged when wording or document structure changes without
changing that behavior. Split behavior gets a new ID; removed behavior retires
its ID, which is never reused.

Test cases declare the IDs they already covered under the former free-form
`covers` field in the `requirements` array in their `checks.json`. `make check`
validates that every ID is unique and every test reference resolves. It does
not infer that every requirement needs a model test or that an unreferenced
requirement is exempt; either decision requires an explicit, sourced change.

`requirements.md` is the traceability index. Its names come from the current
baseline, its test relationships come from the existing case metadata, and its
commit provenance comes from Git history. The normative wording remains in the
baseline alone.

The root `AGENTS.md` makes this workflow mandatory for repository agents and
sets the boundary against unsourced normative decisions. `CLAUDE.md` imports
the same instructions for Claude Code. Keep the process detail here and only
the repository-wide working agreement in the agent files.

## Change workflow

A substantive behavior change starts in `changes/<short-name>/` with three
files:

- `proposal.md`: the problem, goal, non-goals, and compatibility impact;
- `requirements.md`: sourced normative deltas and Given/When/Then scenarios;
- `tasks.md`: implementation and verification work.

Requirements come from the approved request, existing documentation, or commit
history, and name their source. If those sources do not settle a behavior, ask
before recording it as a requirement. The change is ready to implement when
its sourced requirements make the intended behavior and observable acceptance
criteria unambiguous. Implementation updates the baseline, requirement index,
test cases, and user documentation as applicable. Once all tasks are complete,
move the directory to `archive/<date>-<short-name>/`.

Small editorial changes that cannot alter assistant behavior do not require a
change specification. If wording could reasonably change behavior, treat it as
substantive.

## Definition of done

For a substantive change:

1. The problem, goal, and non-goals are documented.
2. Normative requirements name their source; positive or negative scenarios
   express only behavior supported by that source.
3. The compact baseline is updated without duplicating or inventing rule text.
4. Affected model cases reference stable requirement IDs.
5. `make check` passes.
6. Existing relevant A/B model tests are run, or their deferral and reason are
   recorded. A new test obligation is added only when its source is documented.
7. The completed change specification is archived.

Model runs remain evidence, not a deterministic CI gate: they cost tokens, take
time, and are stochastic.
