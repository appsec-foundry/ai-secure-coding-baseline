# Requirements

The baseline does not change here. These requirements bind the example under
`examples/claude-code-gate/`, which is documentation with an executable body.

## GATE-001 Deny only what needs no context

Source: the user's request in this session — build the deny tier discussed, and
only that tier.

The example denies patterns that have no legitimate use in an edit an assistant
just wrote. A construct whose safety depends on deployment, file role, or
surrounding code is not denied, and the example's README names the ones left out
and why.

Acceptance: every rule has a sample it denies and an ordinary sample it allows,
and both run in `make check`.

## GATE-002 Cite the baseline, do not restate it

Source: `AGENTS.md` — normative rule text lives in `secure-coding-baseline.md`;
everything else may explain behavior but must not add or change it.

Each denial names the rule group it comes from and explains the fix in the terms
of that group. The example adds no rule that the baseline does not already carry,
and no rule id it does not define.

Acceptance: a test resolves every cited id against a rule group in
`secure-coding-baseline.md` and fails when one does not exist.

## GATE-003 State the limits where the reader is

Source: `README.md` — the baseline guides an LLM, is not an enforceable control,
and a specification without evidence is guidance rather than a control.

The example says in its own README that it is not part of the baseline, does not
make it enforceable, and cannot see what a single edit does not contain. It
distinguishes what a pattern gate decides, what a warn tier would have to ask,
and what only a model case or a human can judge.

Acceptance: the README carries all three, and the root README points to the
example from the paragraph that raises the limitation.

## GATE-004 Fail visibly, never silently

Source: `secure-coding-baseline.md`, `AISEC-ERRORS-001` and `AISEC-PRESERVE-001`.

A payload the gate cannot read is reported on stderr and allowed, so a harness
change does not block every edit in a session. A finding never repeats a matched
credential into the transcript. The gate carries no environment variable or flag
that switches it off; removing it means editing the settings file.

Acceptance: tests cover the malformed payload, the redacted secret, and the
absence of a bypass; the example's README states the fail-open choice.
