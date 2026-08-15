# Requirements

## CATALOG-001 Self-contained catalog entries

Source: the user's explicit request in this conversation that the requirements
catalog be clear and understandable to both people and AI, rather than looking
like a technically generated reference artifact.

Every baseline rule group must have a readable catalog entry that states when
it applies, summarizes the required behavior without extending it, gives
observable acceptance criteria, and explains the available model evidence and
known gaps.

Acceptance: every baseline ID has one complete catalog entry that a reader can
understand without reconstructing it from a reference table.

## CATALOG-002 Single normative source

Source: the same user request together with the repository's existing rule that
`secure-coding-baseline.md` is the published normative product.

The catalog must make the baseline rule group its normative source. Its summary
and acceptance criteria are explanatory aids and must not create an independent
or conflicting rule.

Acceptance: every entry names its exact baseline rule group and the catalog
states that the baseline remains normative.

## CATALOG-003 Catalog structure guard

Source: the user's request that the specifications be correctly secured and
enforced through guards.

`make check` must reject a missing, duplicate, unknown, malformed, or incomplete
catalog entry and must continue to compare its name, section, and model-case
references with the baseline and case metadata.

Acceptance: mutation tests demonstrate a non-zero check result for each named
structural defect.

## CATALOG-004 Change-spec content guard

Source: the user's request that specification quality be enforced through
guards, and the existing workflow in `specs/README.md`.

`make check` must reject change specifications whose required documents are
empty or structurally incomplete, requirements without IDs, sources, or
behavior text, and archived task lists with unfinished work.

Acceptance: incomplete proposals, requirements, task lists, and archive names
fail targeted mutation tests.

## CATALOG-005 Honest enforcement documentation

Source: the user's request for a clear and traceable specification system.

Documentation must distinguish deterministic structural enforcement, manually
reviewed semantic correctness, and stochastic model evidence without presenting
partial evidence as complete coverage.

Acceptance: the catalog and workflow documentation state each enforcement layer
and label incomplete model evidence as partial.

## CATALOG-006 Explicit confirmation of material security risk

Source: the user's explicit follow-up request in this conversation to ask about
security-relevant changes and risks when the user is making a critical or
insecure decision, checked against the existing baseline.

When a user's selected design is materially riskier than a comparable
alternative, the assistant must state the concrete risk, safer option, and cost,
then obtain explicit confirmation before implementing that choice. This must not
add confirmation prompts when the assistant can simply take a compliant secure
path without changing the user's selected design.

Acceptance: the affected two-turn model case rejects implementation before
confirmation and expects implementation after the user confirms the named risk.

## CATALOG-007 Plain English

Source: the user's explicit follow-up request in this conversation that all
repository text be in English, read as human-written, and avoid unnecessary
prose.

Catalog and workflow text must use direct English and keep each field focused on
information a reader needs to understand or verify the requirement.

Acceptance: new and revised repository text is English, concise, and contains no
duplicated explanation that serves only the document format.
