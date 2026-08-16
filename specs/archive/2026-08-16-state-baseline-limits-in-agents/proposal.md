# State the baseline's limits in the agent instructions

## Problem

`AGENTS.md` says what the repository publishes and how a change runs, but not
what constrains the published text. An agent that never opens `README.md` can
therefore grow the baseline, add tool-specific wording, phrase a rule as a goal,
or drift it toward an application security specification without noticing that
any of those contradicts the product.

It also names only `make check`. Nothing warns that `make test` and
`make test-all` call real models — the full matrix is 60 runs and several hours
— so an agent trying to be thorough can spend that unasked.

And it does not say that `make check` holds `AGENTS.md` itself to a contract,
so an edit to this file can break CI for reasons the file never mentions.

## Goal

`AGENTS.md` states the limits that bind an edit to the baseline text, separates
the free check from the model runs that cost money, and names the contract it is
held to itself.

## Non-goals

Do not restate why the baseline exists or what it covers; `README.md` carries
that and a second copy would drift. Do not change any secure-coding rule, the
workflow under `specs/`, or the harness.

## Compatibility

Documentation only. No rule group changes, so no assistant that loads the
baseline behaves differently.
