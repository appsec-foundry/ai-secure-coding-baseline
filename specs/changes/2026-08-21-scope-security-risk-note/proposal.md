# Consolidate what the security risk note reports

## Problem

A run closed with a two-part security note. The first item reported that a
report generator falls back to "medium" for a severity word it cannot map, which
can downgrade a critical rating in the deliverable — an accuracy defect in
generated output, with no attacker and nothing unprotected. The second item was
a list headed "pre-existing and unchanged": two findings in code the change
never touched.

Both follow the shipped text. `AISEC-OM-001` requires "Report concrete
pre-existing security issues encountered in scope" with no threshold attached,
while `AISEC-REPORT-001` says untouched code does not warrant a note; an
assistant resolves that by reporting the findings under a pre-existing label.
And the materiality test asks only for realistic impact, exploitability, and
exposure, so anything that sounds consequential passes it without a security
property ever being at stake.

Behind both sits the same weakness: the reporting rules have grown one clause
per observed failure — `b9fb85f`, `be6d037`, `e80ce9a` — until three bullets
carry seven stacked obligations and three prohibition lists. Adding a fourth
clause repeats the pattern.

## Goal

One threshold shared by both rules, a materiality test that first asks whether
the issue is a security issue at all, and the accumulated prohibitions folded
into general statements. The rule group ends no longer than it starts.

## Non-goals

Nothing changes about the diff inspection duties, about what a risk item must
say once it qualifies, or about the duty not to silently fix a pre-existing
issue and not to broaden the task into an audit. Self-exculpating wording inside
a risk item gets no rule of its own: an item that argues its own harmlessness
fails the sharpened materiality test.

## Compatibility

Notes get shorter. A pre-existing finding still appears when the delivered work
relies on it or it sits in changed code; a finding in untouched code that the
change does not rely on no longer appears. Non-security defects move out of the
note and into the ordinary answer. The individual prohibitions drop as separate
sentences but stay covered by the general statements that replace them.
