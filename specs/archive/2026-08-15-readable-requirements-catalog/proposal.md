# Make the requirements catalog readable and enforceable

## Problem

`specs/requirements.md` is a machine-checked traceability table, but it does not
explain the requirements. A person or an AI has to follow IDs into the baseline
and infer what each case observes. The existing checks also validate references
and filenames without requiring meaningful catalog or change-spec content.

## Goal

Turn `specs/requirements.md` into a clear catalog that explains every rule
group, when it applies, observable acceptance criteria, model evidence, and
known gaps. Extend the deterministic checks so that this structure, its links
to the baseline and cases, and the minimum content of change specifications
cannot silently disappear. Align the baseline's riskier-design path with its
explicit-override path so that a material security risk chosen by the user is
confirmed explicitly before implementation.

## Non-goals

- Requiring confirmation for secure defaults or ordinary security-relevant work
  that does not introduce a materially riskier choice.
- Treating model cases as deterministic CI gates.
- Claiming that structural checks can prove prose semantically correct.
- Duplicating the complete normative rule text outside the baseline.

## Compatibility

The catalog and maintenance checks become stricter. `AISEC-OM-005` changes from
warn-and-proceed to warn-confirm-and-proceed for materially riskier user choices;
the affected model case becomes a two-turn confirmation case. Other baseline
behavior remains unchanged.
