# Requirements

## IDENT-PREFIX-001 One acronym for the rule set

Source: the user's explicit request in this conversation to use `aiscb` as the
single acronym, together with their approval of `aiscb-0.1.10` as the exact new
baseline ID.

The baseline must identify itself as `aiscb-0.1.10`. Every rule group ID must
read `AISCB-<GROUP>-<NNN>`, keeping the group name and number it has today, so
no behavior changes hands. The heading assistants print for delivered risk must
read `Security note (AISCB baseline)`. The installer's official-name check, the
requirements catalog, the repository documentation, and the model test cases
must use the same acronym.

Acceptance: `AISEC` and `aisec-` appear nowhere outside `specs/archive/`, which
records what the rules were called at the time; `make check` passes, including
its checks that every case names a defined rule ID and every catalog entry
matches its group.

## IDENT-SOURCE-001 Name source and license in the baseline

Source: the user's explicit request in this conversation to reference the
repository in the baseline itself, and the repository's CC BY 4.0 license,
which requires attribution from anyone who copies or adapts the file.

Directly after the baseline ID, the baseline must state
`Source: github.com/appsec-foundry/aiscb (CC BY 4.0).` as metadata. The
statement must carry no imperative, no command, and no verb addressed to the
assistant, so that nothing in it can be read as an instruction to fetch,
install, or update anything.

Acceptance: the line stands between the baseline ID and the sentence about
answering `baseline?`, contains no instruction to the assistant, and the size
and token count in `README.md` are recomputed so that the stated budget covers
the result.
