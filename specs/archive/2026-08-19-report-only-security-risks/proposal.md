# Report only security risks

## Problem

A run of the baseline produced a four-part note for a change that left no
security risk. Later wording made notes rarer, but the output is still triggered
by kinds of changes rather than by risks in the delivered state.

Four requirements still create routine noise.

- A change to a control's strength triggers a note even when it only tightens
  the control and leaves no residual risk.
- Delivering an application triggers a note even when its relevant controls
  were verified and no production blocker remains.
- Four mandatory parts require positive attestations and `none` placeholders.
- Fixed findings trigger the same note as unresolved findings.

The note is meant to be a risk signal. Positive assurance and empty sections
make that signal harder to see in daily work.

## Goal

Keep the mandatory diff review, but emit a security note only when the delivered
state leaves a concrete security risk, a security-relevant verification gap or
assumption, a production blocker, or an accepted security trade-off. Report
each such risk once with its impact, status, and next step.

## Non-goals

Nothing changes about reporting concrete security issues found in scope. A
fixed and verified issue remains visible as a fixed finding in the ordinary
summary, but it is not a residual risk. The internal review of credentials,
reachability, authorization, and transport also stays mandatory.

## Compatibility

Notes become risk-only and lose the fixed four-part format. Consumers that use
the note as an assurance checklist must obtain that evidence from tests or an
explicit release review instead. A production blocker, override, or risky
design decision remains reportable because it leaves a risk to weigh.
