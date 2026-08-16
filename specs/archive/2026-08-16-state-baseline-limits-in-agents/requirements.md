# Requirements

## AGENT-REFERENCE-003 Say what the reference costs if it is not followed

Source: the user's explicit wording in this conversation, and `README.md`, which
states that for agents which do not resolve file references the `AGENTS.md`
reference is an instruction to read the baseline rather than an automatic
import.

The paragraph requiring the baseline must also say that it governs the code
written here exactly as in any installing project, and that the baseline is
referenced rather than embedded, so an agent that does not open it holds none of
the rules.

Acceptance: `AGENTS.md` carries both statements alongside the required
reference, and `make check` still finds the reference.

## AGENT-LIMITS-001 Name the limits that bind the baseline text

Source: the user's explicit request in this conversation to state in `AGENTS.md`
what else an agent needs, and `README.md`, which documents each limit — the
baseline is "deliberately compact", ships to Claude Code, Copilot and every
`AGENTS.md` reader alike, names a mechanism per rule instead of a goal, and "is
not a security specification for the application being built".

`AGENTS.md` must state that an edit to the baseline keeps it compact,
tool-neutral, mechanism-naming, and limited to assistant behavior rather than
application requirements, and must point at `README.md` for the reasoning
instead of repeating it.

Acceptance: `AGENTS.md` carries the four limits and a reference to `README.md`;
no size figure or rationale is duplicated into it.

## AGENT-COST-001 Separate the free check from the model runs

Source: the Makefile header ("Anything that calls a model costs tokens and
hours"), `tests/README.md` ("The full matrix is 60 runs and several hours"), and
`specs/README.md`, which calls the model cases "evidence, not a gate".

`AGENTS.md` must distinguish `make check`, which is free and required after a
change, from `make test` and `make test-all`, which call models, cost tokens and
hours, and are run only when asked or when a change requires the affected cases.

Acceptance: `AGENTS.md` names both, states the cost of the model runs, and does
not present them as a routine step.

## AGENT-SELFCHECK-001 Name the contract this file is held to

Source: `tests/selfcheck.py`, which fails when `AGENTS.md` drops the required
reference or reintroduces a generated baseline block, or when `CLAUDE.md` does
not import both files exactly once, and `specs/README.md`, "What is enforced".

`AGENTS.md` must state that `make check` enforces those conditions on
`AGENTS.md` and `CLAUDE.md`.

Acceptance: `AGENTS.md` names the reference requirement, the generated-copy
prohibition, and the `CLAUDE.md` imports.
