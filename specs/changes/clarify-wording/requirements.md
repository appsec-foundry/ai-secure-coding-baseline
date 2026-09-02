# Requirements

## WORD-001 Development differs only through development tooling

Source: commit df592ff, which closed the opt-in bypass loophole in
`aiscb-ENV-001` and `aiscb-PRESERVE-001`, and the user's approval in this
session.

`aiscb-DEFAULTS-001` allows development to differ from production only through
the tooling `aiscb-ENV-001` defines, explicit and local-only, not through a
weakened control.

Acceptance: a request for a local development convenience that switches off a
control is declined under the existing rules; mocks, fixtures, seed data, and
debug output remain permitted.

## WORD-002 Attribute in the first response after the effect is clear

Source: archived requirement ATTR-002 in
`archive/2026-08-29-attribute-baseline-decisions/`.

`aiscb-ATTR-001` names the baseline in the first response after its material
effect becomes clear, not necessarily the first response of a session.

Acceptance: a conversation where the baseline first matters in a later turn
carries the notice in that turn.

## WORD-003 A one-time code stays away from the requesting client

Source: the first clause of the same `aiscb-AUTH-001` bullet, which delivers
codes and links only through the channel they are addressed to, and commit
8674446.

`aiscb-AUTH-001` forbids returning, displaying, or logging a code to the
requesting client in any form, including a URL; `aiscb-TESTS-001` tests any
URL returned to the requester. A verification link sent through the addressed
channel remains allowed.

Acceptance: an email verification link is implemented and tested without the
code appearing in the response, logs, or any URL the requester receives.

## WORD-004 Scope of pre-existing reports comes from the threshold

Source: archived change `2026-08-23-scope-security-risk-note`, which defines
the qualifying set in `aiscb-REPORT-001`.

`aiscb-OM-001` refers to the reporting threshold without its own scope phrase.

Acceptance: unchanged behavior; the catalog entry for `aiscb-OM-001` mirrors
the sentence.

## WORD-005 Passed checks are not reported

Source: archived change `2026-08-19-report-only-security-risks`, which removed
positive attestations from the report.

`aiscb-REPORT-001` says plainly that a check is not reported merely because it
passed.

Acceptance: a completion report lists no passed checks.

## WORD-006 Cite the OWASP lists by their published names

Source: OWASP GenAI Security Project publications "OWASP Top 10 for LLM
Applications 2026" and "OWASP Top 10 for Agentic Applications 2026".

`aiscb-LLM-001` refers to the current OWASP Top 10 lists for LLM Applications
and for Agentic Applications.

Acceptance: the cited names match documents OWASP publishes.
