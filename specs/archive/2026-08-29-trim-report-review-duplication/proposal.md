# Remove the duplicated application review sentence from the diff inspection

## Problem

The first sub-bullet of `AISEC-REPORT-001` states the same duty twice. Its first
sentence already requires a scan for credential literals across code, seed data,
fixtures, configuration, and docs, and asks whether authentication,
authorization, and transport cover what became reachable. Its second sentence —
"For an application or service, also check transport and bind exposure plus
credential and secret handling" — repeats the credential and transport checks
and adds one item the first sentence does not name: the bind.

The repetition costs words in a rule group the repository already watches for
clause accumulation (`archive/2026-08-23-scope-security-risk-note`). No model
case observes the sentence: every bind and loopback check under `tests/cases`
belongs to `AISEC-DEFAULTS-001` and tests the implementation, not the review
duty.

## Goal

Keep every duty and state it once. The bind joins the list of reachable surfaces
in the first sentence, and the second sentence goes.

## Non-goals

Nothing changes about the materiality threshold, what triggers the
**Security note (AISEC baseline)**, what a risk item must say, or the note's
prohibition list. The rest of the rule group stays as it is.

## Compatibility

The review duty loses its restriction to an application or service, so the
credential and transport check applies to every change rather than to that
subset. That is stricter, not weaker. Consumers that quoted the removed sentence
find its content in the first one.
