# Repository instructions

This repository publishes `secure-coding-baseline.md`. Treat that file as the
single normative product specification. Before changing the baseline, its test
cases, or the specification workflow, read `specs/README.md` and
`specs/requirements.md`. When changing code or configuration, also read and
follow `secure-coding-baseline.md`.

## Specification-driven development

Use the workflow in `specs/README.md` for every change that could alter the
behavior expected from an assistant. Create `proposal.md`, `requirements.md`,
and `tasks.md` under `specs/changes/<short-name>/` before implementing the
behavior change, and archive the directory only after its tasks are complete.
Behavior-neutral editorial changes do not require a change specification.

Derive requirements only from:

- an explicit, approved user request;
- existing normative repository documentation; or
- commit history that clearly establishes the behavior.

Name the source of every requirement. Do not independently introduce normative
behavior, test obligations, exceptions, coverage claims, or scope expansions.
Acceptance scenarios may make sourced behavior observable, but must not add
behavior that the source does not establish. If the sources are ambiguous,
conflicting, or insufficient, ask the user before recording or implementing the
requirement.

Preserve existing requirement IDs when behavior is unchanged. Assign a new ID
only for sourced new behavior or a sourced split of existing behavior; never
reuse a retired ID. Keep normative rule prose in `secure-coding-baseline.md`
instead of duplicating it under `specs/`.

Test cases may reference only requirements they actually exercise. Do not infer
that an unreferenced requirement needs a test, or that it is exempt from one.
Add either conclusion only when its source is documented.

## Verification

Run `make check` after changing the baseline, specifications, test metadata, or
the harness. Run relevant A/B model cases for substantive behavior changes, or
record their deferral and reason in the change tasks. Model runs are evidence,
not a deterministic CI gate.
