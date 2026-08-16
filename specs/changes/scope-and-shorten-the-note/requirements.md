# Requirements

## NOTE-001 Touching a control is not a trigger

Source: the user's request in this session — the note belongs only where a real
security concern exists, not at every change.

A note is owed when the change moves what a control covers, how strongly it
protects, or what is reachable and by whom. Where the change leaves all three as
it found them, it closes without a note, even though it edits security-relevant
code.

Acceptance: a change that preserves or tightens an existing control without
widening its coverage or reach ends without a note, and any concrete finding is
still reported as plain prose.

Example: a parser that silently skipped a malformed allow-list entry now aborts
with an error. Same allow-list, same denials, nothing newly reachable — no note.

## NOTE-002 The note states what a deployer must weigh, not what the diff did

Source: the same request — the note must be short and to the point.

**Implemented** names the controls the reader's decision rests on. It does not
walk through the change, and a control the change left exactly as it was does
not appear at all.

Acceptance: no part of the note restates the change for its own sake.

## NOTE-003 Untouched code and functional uncertainty stay out of every part

Source: the same request — nothing irrelevant in the note.

The existing filter against pre-existing behavior binds all four parts, not
residual risk alone, and extends to uncertainty that costs no security. A
weakness the delivered work rests on stays reportable.

Acceptance: **Left out** names only controls and tests this change was expected
to cover; **Unverified** names only gaps that bear on the security of the
delivered state.

## NOTE-004 One line per part is the default

Source: the same request — short and to the point.

Length is stated as a default rather than an upper bound: one line per part,
a further bullet only where it earns its place, roughly five as the ceiling for
a delivered application or service.

Acceptance: a note for a change touching a single control reads as four short
lines.
