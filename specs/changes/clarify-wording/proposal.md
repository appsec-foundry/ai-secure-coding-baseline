# Clarify six wordings

## Problem

A content review of the baseline found six sentences whose wording drifted
from the intent their sources record, or that name something inexactly:

- `aiscb-DEFAULTS-001` still allows "weaker development settings", the
  loophole commit df592ff closed in `aiscb-ENV-001` and
  `aiscb-PRESERVE-001`.
- `aiscb-ATTR-001` asks for the notice "in the first response"; the archived
  requirement ATTR-002 asks for the first response after the baseline's effect
  becomes clear.
- `aiscb-AUTH-001` and `aiscb-TESTS-001` forbid a one-time code in a "URL",
  which reads as forbidding verification links altogether.
- `aiscb-OM-001` says "encountered in scope", promising more reports than the
  threshold in `aiscb-REPORT-001` admits.
- `aiscb-REPORT-001` says "attest their absence" with no clear referent.
- `aiscb-LLM-001` cites one OWASP title that does not exist; OWASP publishes
  separate Top 10 lists for LLM Applications and for Agentic Applications.

## Goal

Make each sentence say what its source intended, at the smallest token cost.

## Non-goals

No version change. No new rule, exception, or test obligation. No change to
which risks qualify for the security note.

## Compatibility

No model check names any of the changed phrases. The development-settings
wording tightens: a relaxed control that is not development tooling is no
longer covered by "explicit and local-only".
