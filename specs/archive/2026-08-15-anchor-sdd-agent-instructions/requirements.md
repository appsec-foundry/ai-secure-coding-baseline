# Requirements

## AGENT-SDD-001 Repository-wide SDD instruction

Source: the user's explicit request on 2026-08-15 to anchor specification-driven
development in the agent instructions.

The repository-wide agent instructions MUST require the workflow documented in
`specs/README.md` for changes that could alter expected assistant behavior.

### Scenario: substantive baseline change

- Given an agent is asked to change expected assistant behavior
- When it prepares the repository change
- Then it creates and follows the change specification before implementation

## AGENT-SDD-002 No unsourced requirements

Source: the user's explicit instructions on 2026-08-15 to derive requirements
from commits and documentation, not invent them, and discuss unresolved choices
before adding them.

Agents MUST derive requirements only from an approved user request, existing
normative repository documentation, or commit history that clearly establishes
the behavior. They MUST ask before recording or implementing a normative choice
that those sources do not settle.

### Scenario: ambiguous source

- Given the available request, documentation, and history permit different
  normative behaviors
- When an agent writes the change requirements
- Then it asks the user instead of selecting or adding a behavior itself

### Scenario: sourced requirement

- Given an approved request unambiguously defines a behavior
- When an agent writes and implements the change specification
- Then it may proceed without a redundant approval checkpoint

## AGENT-SDD-003 Shared tool coverage

Source: `README.md` documents root `AGENTS.md` for shared agent support and a
Claude Code `@` import for project instructions.

Codex-compatible agents MUST receive the maintenance workflow from the root
`AGENTS.md`, and Claude Code MUST import that file from root `CLAUDE.md`.

### Scenario: repository session

- Given Codex or Claude Code starts in the repository
- When it loads project instructions
- Then the SDD workflow and sourcing boundary are included in its context

## AGENT-SDD-004 No normative duplication

Source: `README.md` and `specs/README.md` identify
`secure-coding-baseline.md` as the single normative, distributable artifact.

Agent instructions MUST point to the baseline and specification documents
instead of reproducing their normative contents.

### Scenario: future workflow edit

- Given the SDD process changes without changing secure-coding behavior
- When the agent instructions are updated
- Then the baseline rule prose is not copied into the instruction file
