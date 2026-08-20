# Requirements

## REF-001 Every rule deposits its result in the security note

Source: `secure-coding-baseline.md`, rule groups `AISEC-OM-004` and
`AISEC-OM-005`, which since `dca08bd` name the security note, and
`AISEC-REPORT-001`, which defines no other note part.

A rule that requires a result to be recorded names the security note. No rule
refers to a note part that `AISEC-REPORT-001` does not define.

Acceptance: seeded demo accounts appear in the security note as what keeps the
work out of production, and the baseline contains no reference to a named note
part.
