# Require a next action or accepted status

## Problem

`AISEC-REPORT-001` lets a risk item close with a disclaimer instead of a step.
A run reported two real agent-permission findings and ended the item with
"pre-existing and outside this task" — neither a corrective action nor an
accepted status, so the reader learns what is wrong but not what happens next.

The shipped rule text permits it. `WEIGHT-002` of the archived change
`2026-08-20-risk-weighted-security-reporting` attached the next action to a
condition ("only when it adds information") and that condition reached the
baseline in `b9fb85f`. `WEIGHT-004` of the same change requires the opposite for
exactly these items, and the catalog entry still calls a reported risk
actionable. Since `WEIGHT-001` restricts the note to material risks, the
condition is never the right reading and only weakens the item.

## Goal

Bring the rule text back in line with `WEIGHT-004`: the default risk item states
scope, consequence, and the next action or accepted status.

## Non-goals

Nothing changes about what triggers a note, what counts as material, how risks
are ordered and grouped, or how much detail a serious risk gets. The change does
not add an obligation to mark a risk as pre-existing. The requirements catalog
and the model cases already carry this behavior and stay as they are.

## Compatibility

Risk items grow by a clause where they previously stopped after the consequence.
The sentence budget is unchanged, and the rule text becomes shorter.
