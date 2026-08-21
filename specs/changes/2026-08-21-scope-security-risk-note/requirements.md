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
