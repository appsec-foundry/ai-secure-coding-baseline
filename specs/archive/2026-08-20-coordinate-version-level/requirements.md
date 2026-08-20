# Requirements

## VERSION-LEVEL-001 Patch is the default

Source: the user's explicit request in this conversation that routine version
increments change only the patch level.

Every normative baseline revision increments the patch component by default.
Repository-only changes still do not change the baseline version.

Acceptance: the pending revision identifies itself as `aisec-0.1.1`, and the
README documents patch as the default for normative changes.

## VERSION-LEVEL-002 Minor and major require agreement

Source: the user's explicit request in this conversation that major and minor
must not increase automatically and instead require coordination.

The assistant must not infer a minor or major increment from the contents or
compatibility of a change. It uses either level only after the user explicitly
agrees to that version decision.

Acceptance: the README requires explicit agreement for minor and major versions
and contains no rule that raises either level automatically.
