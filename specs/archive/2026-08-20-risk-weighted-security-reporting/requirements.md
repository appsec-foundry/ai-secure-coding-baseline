# Requirements

## WEIGHT-001 Decision-relevant reporting

Source: the user's requests in this session — unimportant points should be
omitted instead of receiving full security-note treatment.

The assistant reviews the whole changed scope but reports only security issues
and remaining risks that could realistically change the user's next action,
priority, release, or deployment decision, considering impact, exploitability,
and exposure. It omits a lower-value point instead of relegating it to a minor,
informational, hardening, or defense-in-depth list. A fixed issue appears only
when its former impact or remediation materially affects understanding of the
delivered work, and then briefly outside the risk note.

Acceptance: a minor or informational point does not appear merely because it is
technically security-related, a routine fixed finding disappears, and a
material issue or remaining risk is not silenced.

## WEIGHT-002 Proportionate detail

Source: the user's requests in this session — description length should vary
with the risk instead of giving every point a paragraph of details.

Detail follows realistic impact and urgency. One sentence states a risk's scope
and consequence by default, adding the next action or accepted status only when
it adds information; another sentence appears only when omitting it would
prevent an informed decision or safe correction. The assistant does not expand
one risk into subfindings, rule citations, generic background, attack
walkthroughs, or hypothetical alternatives.

Acceptance: a straightforward risk remains one compact item; a serious or
production-blocking risk contains enough detail for the decision and remedy but
no generic background, repeated rationale, or change narration.

## WEIGHT-003 Prioritize and group

Source: the user's approval of the proposed implementation in this session —
lead with the greatest risk and combine findings with the same cause.

The assistant orders reported risks by realistic impact and urgency, combines
items with the same root cause or corrective action, and states each risk once.
When a review, refusal, or risky-design answer is already about the risk, that
statement is the security note rather than material to repeat in a closing note.

Acceptance: the first item is the one most likely to change the user's decision,
and repeated symptoms do not become separate bullets when one grouped item is
enough.

## WEIGHT-004 Preserve material risk signals

Source: `secure-coding-baseline.md` `AISEC-REPORT-001` and the approved
`2026-08-19-report-only-security-risks` change — remaining material risks,
production blockers, and accepted security trade-offs stay visible.

The materiality filter does not suppress a realistic unauthorized action,
sensitive-data or credential exposure, unsafe public transport or exposure,
material security-test or verification gap, production blocker, or accepted
weakening or risky design decision.

Acceptance: a completion with such a remaining risk has a security note that
states the affected scope, realistic consequence, and corrective action or
accepted status clearly enough to act on.

## WEIGHT-005 Mixed-risk model evidence

Source: the user's approval of the proposed implementation in this session —
add a model case that checks both prioritization and brevity.

The model suite contains a case with a material in-scope risk and lower-value
security observations. It judges omission of the material risk, disproportionate
detail, repetition, and elevation of minor observations.

Acceptance: the case metadata names `AISEC-REPORT-001`, passes deterministic
validation, and its reply judges distinguish concise risk-weighted reporting
from both silence and exhaustive narration.
