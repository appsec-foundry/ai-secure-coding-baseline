# Requirements

## SCOPE-001 One reporting threshold for pre-existing issues

Source: the user's request in this session, after a run reported two findings in
untouched code under the heading "pre-existing and unchanged"; and the shipped
text of `AISEC-REPORT-001`, which already excludes untouched code from the note.

`AISEC-OM-001` states its reporting duty without a threshold, so it reads as an
independent obligation next to the reporting rule. It refers to the threshold in
`AISEC-REPORT-001` instead, and that threshold says when a pre-existing weakness
qualifies: the delivered work relies on it, or it sits in code the change
touched or the user asked to have reviewed. The review case keeps a read-only
review task reporting its findings, where nothing is changed at all.

Acceptance: a finding in untouched code that the delivered work does not rely on
appears in no note, and neither rule can be read as requiring it.

## SCOPE-002 Security relevance is tested before materiality

Source: the user's request in this session, after a run reported a severity
mapping fallback in a report generator as a security risk.

Materiality currently asks only for realistic impact, exploitability, and
exposure. It first asks whether an attacker or untrusted input could turn the
issue into a concrete loss of confidentiality, integrity, or availability.
Correctness, accuracy, and quality defects are reported outside the note if the
reader needs them at all.

Acceptance: a defect in generated output with no attacker and no unprotected
asset does not appear in the note, whatever its consequence for the reader.

## SCOPE-003 The reporting rules read as general statements

Source: the user's request in this session that the baseline stay generic and
consistent rather than accumulate one clause per observed failure; and the size
budget in `README.md`.

The reporting bullets of `AISEC-REPORT-001` state what belongs in the note and
what a risk item says, with the incident-specific prohibitions folded into those
statements rather than listed one by one. The behavior each prohibition carried
survives; its separate sentence does not.

Acceptance: the rule group is no longer than before the change, and every
behavior the prohibitions covered — no `none` placeholder, no assurance about
working controls, no attack walkthrough, no rule citation, no change narration,
no subfindings — still follows from the text.

## SCOPE-004 A delivered adverse security change triggers the note

Source: the user's requests in this session that risks appear only when the
implementation creates a concrete application-security risk, materially
weakens an important security control, or has an equivalent adverse security
effect.

The residual-risk note appears only for a security-relevant, material risk that
the delivered code, configuration, or design creates or materially worsens.
That includes weakening a material security control, making a pre-existing
weakness relevant to a new or changed path, accepting a security trade-off or
override, or changing a critical security boundary while its concrete dangerous
failure mode remains materially unverified. A fixed issue and a pre-existing
issue the implementation neither worsens nor makes relevant do not trigger the
note. An expressly requested risk review or refusal gets no additional note; a
confirmed risky-design decision uses the named note and does not repeat the risk
elsewhere.

Acceptance: a correctness-only change, a protected and verified security
change, and a pure control tightening produce no note. A delivered authorization
bypass, materially weakened control, newly relied-on material weakness, accepted
override, or materially unverified dangerous failure mode in a changed critical
boundary remains visible once.

## SCOPE-005 Verification status is not a security risk by itself

Source: the user's request in this session after a run reported an unrun full
suite and unexamined callers as a security risk for a correctness-only
`context-mode` change whose twelve focused tests passed.

An unrun test or suite, incomplete coverage, unexamined callers, and general
uncertainty are ordinary test status. They become a residual security risk only
when they leave the concrete dangerous failure mode of a changed critical
security boundary materially unverified under `SCOPE-004`; incomplete
verification alone establishes no security relevance.

Acceptance: the focused test command may be reported outside the note, but the
unrun full suite and unexamined callers do not produce a security-risk heading
or item when no qualifying adverse security change remains.

## SCOPE-006 Attribute a baseline-added note

Source: the user's request in this session that the title identify when the
security-risk note came from the baseline.

When `AISEC-REPORT-001` adds its residual-risk note to an ordinary completion,
the heading is `Security risks (AISEC baseline)`, without a version or rule ID.
The heading does not claim that the baseline deterministically found the risk.
An expressly requested security review uses the answer structure appropriate to
that request and receives no additional baseline note.

Acceptance: a baseline-required residual-risk note identifies its source; a
completion without a qualifying risk contains neither the heading nor an empty
placeholder, and an explicit risk review has no duplicate closing note.
