# Repository instructions

This repository publishes `secure-coding-baseline.md`. That file is the product:
the rules an assistant follows. Everything else exists to keep it correct.

Before doing any repository work, read and follow
[`secure-coding-baseline.md`](secure-coding-baseline.md). It is the normative
source for assistant behavior: it governs the code you write or change here
exactly as in any project that installs it. It is referenced, not embedded —
open it, or the rules are not in your context at all.

[`README.md`](README.md) explains why the baseline exists and what it covers.
Keep it clear, concise, and written for users: lead with the action and outcome,
avoid implementation details or extended explanations unless they are needed
for safe use, a necessary decision, or troubleshooting, and do not duplicate
the code's internal workflow.

Four limits from it bind every edit to the baseline text:

- It stays compact. Size is a criterion, not only correctness; the README states
  the current budget. After every change to `secure-coding-baseline.md`,
  recompute its file size and GPT token count with the `o200k_base` encoding and
  update both values in `README.md`; never carry the previous measurements
  forward by assumption.
- It stays tool-neutral. The same text ships to Claude Code, Copilot, Codex, and
  anything else that reads an `AGENTS.md`, so no rule may depend on one tool.
- Every rule names a mechanism, not a goal. "Authorize on the server" works;
  "be security-aware" does not.
- It governs how an assistant behaves. It is not a security specification for
  the application being built, and application-specific requirements do not
  belong in it.

Use specification-driven development for every change to
`secure-coding-baseline.md` that could alter how an assistant behaves. Read
[`specs/README.md`](specs/README.md) before changing the baseline—it describes
how baseline changes run here. Changes limited to repository tooling,
configuration, workflow, documentation, the harness, or tests do not get a
change specification when the normative baseline stays unchanged.

Four rules hold no matter how small the baseline change looks:

- Requirements come only from an explicit user request, existing repository
  documentation, or commit history that clearly establishes the behavior. Name
  the source. If none of them settles a question, ask instead of deciding it.
- Normative rule text lives in `secure-coding-baseline.md`. The readable
  requirements catalog and change specifications live under `specs/`; they may
  explain behavior but must not add or change it.
- Nothing under `specs/` is written without the user's explicit approval.
  Propose the entry — the requirement, its source, the file it lands in — and
  wait for an answer. Reading the specs, and pointing out that one is wrong or
  missing, needs no approval. `scripts/spec_guard.py` turns that sentence into a
  permission prompt for identifiable writes from tools that support hooks.
  `.claude/settings.json` registers it for Claude Code when Claude Code is
  launched from the repository root; a session launched below the root does not
  inherit that project hook. A command hook that cannot start or times out
  produces no decision, so the instruction remains authoritative where the
  hook or its normal permission fallback cannot establish the effect.
- Do not change the baseline ID or version unless the user explicitly approves
  the exact new value. A request to change the baseline text is not version
  approval.

Run `make check` after changing the baseline, the specs, test metadata, or the
harness. It calls no model, takes seconds, and also holds this file to its own
contract: `AGENTS.md` must require agents to read and follow the baseline
through the reference above, must not carry a generated copy of it, and
`CLAUDE.md` must import both files exactly once.

The remote quick start treats `setup.sh` as a content-pinned bootstrap. Whenever
`setup.sh` changes, recompute its SHA-256 and update the inline value in
`README.md`; `scripts/test_install.py` enforces that match. When the download URL
is pinned to a bootstrap commit rather than `main`, it must name the commit that
contains that exact `setup.sh`, and a changed bootstrap requires both a new
commit reference and a new SHA-256. Because the commit is only known after it is
created, make that URL update in a follow-up documentation commit.

`make test` and `make test-all` are a different matter: they run the cases
against real models. The full matrix is 60 runs and several hours of tokens.
Run them when the user asks, or for the cases a change affects — never as a
routine check. They are evidence, not a gate.
