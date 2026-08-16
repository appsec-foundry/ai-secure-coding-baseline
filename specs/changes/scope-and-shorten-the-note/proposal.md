# Scope and shorten the security note

## Problem

A run of the current baseline produced a four-part note for a change that moved
nothing a deployer must weigh: a silent no-op became an explicit abort, a header
line gained two fixed labels, and a guard test was added. Every control kept the
coverage, strength, and reach it already had.

Four wordings let that happen.

- The trigger fires on the diff *touching* a control or trust boundary, whether
  or not anything about that control changed. Almost every edit near input
  handling qualifies.
- Nothing forbids narrating the change, so **Implemented** became a walkthrough
  of the diff instead of the controls the reader's decision rests on.
- The filter against pre-existing behavior is worded for residual risk only, so
  **Left out** listed a neighbouring file the change never touched.
- **Unverified** carried functional uncertainty that costs no security — whether
  a model would copy a header value verbatim.

The note is meant to be a signal. Written at every change, and padded to fill
four parts, it stops being one.

## Goal

The note appears where the delivered state actually changed for a deployer, and
where it appears it is short: one line per part by default, no diff narration,
no untouched code, no process uncertainty.

## Non-goals

Nothing changes about reporting concrete security issues found in scope. That
stays plain prose and is owed whether or not a note applies. The four parts, the
three deployer axes, and the production-use verdict stay as they are.

## Compatibility

Notes get rarer and shorter. Situations that already required one — a delivered
application or service, a widened surface, a found issue, an override — still
require one, with the same parts.
