# Point the prototype rule at the note that exists

## Problem

`AISEC-OM-002` tells an assistant that seeded demo accounts "belong in the
Production use verdict". That verdict was a named part of the four-part note
`AISEC-REPORT-001` defined until `dca08bd`. The same commit removed the four
parts and moved `AISEC-OM-004` and `AISEC-OM-005` to "the security note", but
left `AISEC-OM-002` pointing at the part it had just deleted.

An assistant reading the rule today is sent to an artifact the baseline no
longer defines.

## Goal

Name the artifact that exists, so the prototype rule, the override rule, and the
design-decision rule all deposit their result in the same place.

## Non-goals

Nothing changes about when seeded accounts are permitted, what has to be said
about them, or what makes a note appear. `AISEC-REPORT-001` keeps its own rule
about when to state that production use is unsafe or conditional.

## Compatibility

Assistants that produced a separate "Production use" heading for this rule now
state the same fact inside the security note. The statement itself is unchanged.
