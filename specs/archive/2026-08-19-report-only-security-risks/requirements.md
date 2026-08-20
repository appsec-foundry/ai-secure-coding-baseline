# Requirements

## NOTE-001 A remaining risk is the only note trigger

Source: the user's requests in this session — only real risks should be emitted.

The assistant always reviews the diff, but emits a security note only when the
delivered state leaves a concrete security weakness, a security-relevant
verification gap or assumption, a production blocker, or an accepted security
trade-off. Touching, adding, or tightening a control and delivering an
application are not triggers on their own.

Acceptance: a fully protected and verified security-relevant change ends
without a security note; a change with a remaining security risk reports it.

Example: a new authenticated endpoint with server-side resource authorization,
bounded input, protected transport, and passing negative tests creates no note
when no applicable risk or verification gap remains.

## NOTE-002 Every note item is an actionable risk

Source: the same requests — the output should contain only actual risks.

Each note item names one risk, its affected location or scope, realistic impact,
status, and next step. A production-use statement appears only when a risk makes
production unsafe or conditional.

Acceptance: every statement in the note can change a security or deployment
decision; no affirmative production verdict or successful-control narration
appears.

## NOTE-003 Empty and positive assurance stays silent

Source: the same requests — daily output should not be padded.

The note has no mandatory parts. It contains no `none` placeholders, lists of
implemented controls or successful tests, untouched code, generic process or
tool uncertainty, or uncertainty that has no security impact. For a delivered
application, authentication and authorization, transport and exposure, and
credentials and secrets appear only where an axis contains a reportable risk.

Acceptance: no note is emitted when every applicable item would be positive or
empty, and a risk-bearing note contains no filler.

## NOTE-004 Fixed findings are not residual risks

Source: the user's approval in this session — fixed findings stay transparent
outside the risk-only note.

A concrete issue encountered in scope is still reported with its location,
impact, status, and next step. When it was fixed and its security property was
verified, it is reported as a fixed finding in the ordinary summary and neither
triggers nor appears in a security note unless a residual risk remains.

Acceptance: a fixed and verified issue remains visible, but a response with no
remaining security risk contains no security note.
