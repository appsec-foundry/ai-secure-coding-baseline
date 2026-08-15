# Adopt specification-driven development

## Problem

The baseline already acts as a normative specification and the model cases as
executable examples, but their relationship is expressed through free-form
section names in `covers`. The suite cannot detect a misspelled, renamed,
or removed requirement reference. Changes also have no durable record of their
intent, non-goals, or acceptance criteria.

## Goal

Make the existing workflow explicitly specification-driven with stable
requirement IDs for the existing rule groups, machine-checked test references,
commit provenance, and a lightweight proposal, requirements, tasks, and archive
lifecycle for substantive changes.

## Non-goals

- Splitting the distributed baseline into multiple runtime files.
- Generating the baseline from duplicated requirement prose.
- Requiring a change specification for behavior-neutral editorial work.
- Turning stochastic, costly model evaluations into a hard CI gate.
- Retrofitting detailed change histories that were not recorded at the time.
- Declaring new test obligations or test coverage not already documented.

## Compatibility

The baseline remains one Markdown file at the repository root. Requirement IDs
add visible labels but do not change the rules. Existing test execution and
report formats remain unchanged; only suite metadata and self-validation become
stricter.
