# Requirements

## LOWERCASE-IDENTITY-001 Use one lowercase acronym

Source: the user's explicit request in this conversation to use `aiscb`, not
`AISCB`, throughout the project while retaining the `s` for "Secure".

The baseline must keep the exact ID `aiscb-0.1.10`. Every current rule group ID
must read `aiscb-<GROUP>-<NNN>`, keeping its group name and number. Current
attribution text, the risk heading, the requirements catalog, repository
documentation, tools, and test cases must use the same lowercase acronym.

Acceptance: `AISCB` appears only in archived records that describe the earlier
uppercase identity; all current surfaces use `aiscb`, and `make check` passes.
