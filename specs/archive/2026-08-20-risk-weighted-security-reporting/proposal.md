# Risk-weighted security reporting

## Problem

The risk-only note removed empty sections and positive assurance, but reporting
is still exhaustive. Every concrete issue and every remaining risk carries the
same required fields, regardless of whether it changes a user's decision. That
makes minor, informational, and already resolved points compete with serious
risks and encourages long completion messages.

## Goal

Keep the internal review complete while making user-facing reporting selective.
Report material risks first, scale detail to realistic impact and urgency, group
risks with the same cause, and omit points that do not affect a reasonable
security, remediation, release, or deployment decision.

## Non-goals

The change does not weaken the controls the assistant must implement, excuse a
material risk, or turn a scoped review into a full audit. It changes what the
assistant surfaces and how much detail it gives, not what it checks internally.

## Compatibility

Completion messages will no longer enumerate negligible or informational items,
or routine fixed findings with no material residual risk. Consumers that need an
exhaustive finding inventory must obtain it from a dedicated review rather than
treating every coding-task completion as one.
