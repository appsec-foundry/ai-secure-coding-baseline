# Testing the baseline

The suite measures whether aiscb changes assistant behavior. It runs the same
task with and without the project baseline, then compares the violations found
in both arms.

- A **case** contains a prompt sequence, optional fixture, and checks.
- An **agent run** executes one case once with one tool in one arm. It may have
  several conversation turns.
- A **matrix** is the selected combination of cases, tools, arms, and repeats.
- `control` has no project baseline; `baseline` installs the current
  `secure-coding-baseline.md`. User-level instructions still affect both arms.

## Run the suite

Start with the smallest target that answers your question:

```bash
make check                                    # validate everything; no model calls
make dry-run                                  # show the matrix; spend nothing
make test-smoke                               # verify that the harness works
make test-quick                               # cheapest useful comparison
make test-rule RULE=aiscb-REPORT-001          # cases for one rule group
make test                                     # all cases with the default tool
make test-all                                 # all cases with Claude and Codex
```

Use `test-rule` after changing a baseline rule; the selected cases come from
their `requirements` entries in `checks.json`. Broad groups may select much of
the suite, so run `make dry-run` first. Pass runner options through `ARGS`, for
example:

```bash
make test-rule RULE=aiscb-LIMITS-001 ARGS="--repeats 5"
make test-quick ARGS="--no-judge"
```

Every model target runs `make check` first. That command validates cases,
requirement mappings, validators, and the runner without calling a model; it
also runs on every push and pull request.

Claude runs require `claude` on `PATH`. Codex runs additionally require
`codex`; Claude still performs the judge checks. Temporary projects are created
under `$TMPDIR`. Successful ones are removed unless `--keep` is used; failed or
incomplete ones are retained. Reports are written to
`tests/results/<timestamp>/` and are not committed.

## Choose an appropriate matrix

Cost grows with `cases × tools × arms × repeats`. Multi-turn cases add turns,
judge checks add calls, and preflight adds one short call per tool and arm.
Three repeats are the default because model output varies.

| Target | Agent turns | Approximate cost | Typical duration |
| --- | ---: | ---: | ---: |
| `make test-smoke` | 2 | USD 1.50 | 5–10 min |
| `make test-quick` | 24 | USD 19 | 30–45 min with `--parallel 3` |
| `make test` | 162 | USD 110 | about 3 h with `--parallel 3` |
| `make test-all` | 324 | USD 140 on the Claude side | many hours, sequential |

These estimates are dated and model-dependent. Use the provider's reported
cost to remeasure after a model or pricing change. `make dry-run` is the
authoritative view of the matrix before execution. `--no-judge` saves judge
calls while deterministic checks still run; selecting fewer cases saves more
but also reduces evidence.

`test-smoke` runs one case once per arm and checks the entire path from preflight
through reporting. One repeat only proves that the harness works. `test-quick`
uses one representative case per direction with three repeats. A full `test`
runs every case; `test-all` repeats that across Claude and Codex.

## What happens during a run

1. **Preflight** asks one throwaway session per tool and arm `baseline?`.
   `control` must report no baseline, while `baseline` must report the current
   one. Any mismatch stops the matrix before paid work begins.
2. The runner copies the fixture into an isolated temporary directory.
3. The baseline arm receives aiscb through the tool's project instruction
   mechanism: `.claude/rules/secure-coding-baseline.md` for Claude Code or
   `AGENTS.md` for Codex. This installed file is excluded from scoring and the
   fixture diff.
4. Both arms receive the same prompt sequence. The runner records replies,
   resulting text files, and fixture changes.
5. Deterministic checks inspect patterns, changed files, note counts, and
   project commands. A judge evaluates questions that require interpretation.
6. The report compares violations per check. Lower is better.

### Why preflight matters

Both arms use the same account and machine. A user-level aiscb install would
put the baseline into `control`; a broken project install would remove it from
`baseline`. Either failure makes the arms look artificially similar.

Therefore aiscb must not be installed at user level for the tool under test.
Remove its import from `~/.claude/CLAUDE.md` or its content from
`~/.codex/AGENTS.md` before measuring. Other user-level instructions still
reach both arms and may influence the result. The preflight reports the exact
mismatch and stops.

## Models and judge behavior

Claude agent runs and the judge are pinned to `claude-sonnet-4-6`; Codex uses
its own default. The report records the models used. Run `--model` with one tool
at a time because model names are provider-specific; use `--judge-model` to
change only the judge.

The judge receives the final text files and all replies from one completed run,
but not the fixture diff or log. Its code bundle is capped at 200 KB. Questions
are judged up to three times: the third vote is skipped when the first two
agree. `pass` and `fail` votes count, while `unclear` and errors abstain; ties
remain unscored. Incomplete agent runs are not judged or scored.

## Test coverage

The suite currently covers these scenarios:

| Area | Cases | Main behavior measured |
| --- | --- | --- |
| Greenfield applications | `greenfield-order-app`, `greenfield-untrusted-input`, `greenfield-web-api-hardening`, `greenfield-llm-output-validation` | Credentials, stable keys, ownership, input handling, browser and transport controls, limits, model-output validation, safe sinks, and negative tests |
| Dependencies under pressure | `greenfield-hallucinated-package` | An unverifiable package is not presented as established fact |
| Existing applications | `existing-retrieved-instructions`, `existing-scoped-change`, `existing-preserve-only-change`, `existing-protected-endpoint`, `existing-targeted-verification`, `existing-risk-weighted-report` | Prompt-injection resistance, narrow changes, authorization and input tests, and proportionate risk reporting |
| Pressure to weaken controls | `existing-pressure-weaken`, `existing-pressure-tls-verify` | CSRF and certificate verification remain enabled when safe fixes exist |
| Design choices | `design-riskier-choice`, `design-accepted-risk-note`, `design-browser-basic-auth` | Risk, safer alternative, cost, confirmation, attribution, and accepted-risk reporting occur in the correct order |
| Explicit overrides | `override-demo-app`, `override-hardcoded-secret` | Safe portions are delivered while prototype credentials and real secrets remain within the baseline's limits |

`specs/requirements.md` records which rule groups each case supports and where
coverage gaps remain. `make check` rejects invalid IDs and catalog mismatches,
but changes to the meaning of a case still require human review.

## Add or change a case

A case has this structure:

```text
tests/cases/my-case/
├── prompt.md        first user turn
├── followup-1.md    optional next turn in the same session
├── checks.json      rationale, requirements, and checks
└── fixture/         optional starting project
```

Write the prompt as a natural user task without naming the behavior being
tested. Numbered follow-ups continue the same session. Codex resumes the newest
session process-wide, so the runner rejects multi-turn Codex matrices with
`--parallel > 1`.

Every `checks.json` needs:

- `mode`: `greenfield` or `existing`;
- a non-empty `why` explaining the case;
- `requirements`: the aiscb rule groups exercised by the case; and
- at least one observable check.

The prompt files define the real conversation. Fields such as `turns`,
`scope_note`, and `reads_inverted` only document how to interpret it.

### Available checks

| Mechanism | Use it for |
| --- | --- |
| Conversation contract | Required behavior and security-note count on each turn |
| Required or forbidden pattern | Exact text or code that should be present or absent |
| Judge question | Meaning that a pattern or command cannot establish |
| Scope check | Files the run must or must not modify |
| Project command | Executable behavior of the finished fixture |

Conversation contracts must cover every turn exactly once. Give turn-specific
judge questions stable IDs so reports remain comparable when wording improves.
Use patterns mainly for code or data; prose can mention a forbidden construct
while correctly explaining that it was not created. Restrict file patterns with
`in` where possible.

Judge questions describe a possible defect: `fail` means the defect exists,
`pass` means it does not, and `unclear` means the evidence is insufficient.
Top-level judge keys derive from the question, so changing the wording begins a
new history.

Scope checks compare fixture hashes before and after the run:

```json
"must_modify": ["server.js"],
"must_not_modify": ["auth.js"]
```

Use `verify` to test the finished project and `fixture_precondition` to prove
the untouched fixture starts in the required state:

```json
"verify": {"cmd": "npm test", "expect_exit": 0},
"fixture_precondition": {
  "cmd": "npm test",
  "expect_exit": 1,
  "why": "the case depends on the suite starting red"
}
```

Without a precondition, a fixture repair can silently turn a case into a no-op.

### Conversation order and security notes

Some requirements concern sequence rather than final code. For example, a
riskier design must be explained with its safer alternative and cost, then wait
for explicit confirmation, and only afterward be implemented and recorded as
an accepted risk. Conversation contracts check each turn separately; patterns
handle fixed wording, while judge questions handle meaning.

Use an exact `security_note_count` when the case determines the expected number.
Secure changes, safe refusals, and findings already stated in a requested review
expect zero; accepted or material remaining risks expect one. Greenfield cases
that may legitimately finish with zero or one use shared judge questions to
detect missing, unnecessary, or incorrectly structured notes instead.

## Read the results

`report.md` contains the aggregate comparison. `runs.json` contains individual
findings, judge votes and evidence, regex locations, and retained working
directories.

Report cells show `violations / scored runs`:

| Check | Tool | control | baseline | p |
| --- | --- | --- | --- | --- |
| default-password-literal | claude | 4/5 | 0/5 | 0.02 |

- More violations in `control` is the intended effect.
- Both columns near zero means the model already handled that check.
- Both columns high means the baseline did not change behavior reliably.
- More violations in `baseline` may indicate a regression.

`p` is a one-sided Fisher exact test for the intended direction. With only
three repeats, even `3/3` versus `0/3` gives `p = 0.05`; treat it as protection
against overreading a one-run difference, not as strong statistical evidence.
It does not test regressions.

Incomplete runs are listed separately. Unclear, tied, or errored judge results
are unscored, so denominators can differ. Inspect `runs.json` before drawing a
conclusion.

The report also shows what each arm reported during preflight and the average
number of security notes against the expected count. Interpret that count per
case: zero is correct for a secure change, while one is correct when the case
accepts a material risk.

## Limits

- A session quota stops the whole matrix; otherwise later empty responses could
  be mistaken for clean passes.
- User-level Claude and Codex instructions affect both arms, and Claude's also
  affect the judge. Preflight only detects whether aiscb itself leaked between
  arms.
- Pattern checks can produce false positives, especially on explanatory prose.
  Prefer code and data patterns and leave semantic wording to the judge.
- Model results are evidence, not a CI gate.
