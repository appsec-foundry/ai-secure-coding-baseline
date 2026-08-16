# Repository instructions

This repository publishes `secure-coding-baseline.md`. That file is the product:
the rules an assistant follows. Everything else exists to keep it correct.

Before doing any repository work, read and follow
[`secure-coding-baseline.md`](secure-coding-baseline.md). It is the normative
source for assistant behavior: it governs the code you write or change here
exactly as in any project that installs it. It is referenced, not embedded —
open it, or the rules are not in your context at all.

[`README.md`](README.md) explains why the baseline exists and what it covers.
Four limits from it bind every edit to the baseline text:

- It stays compact. Size is a criterion, not only correctness; the README states
  the current budget.
- It stays tool-neutral. The same text ships to Claude Code, Copilot, Codex, and
  anything else that reads an `AGENTS.md`, so no rule may depend on one tool.
- Every rule names a mechanism, not a goal. "Authorize on the server" works;
  "be security-aware" does not.
- It governs how an assistant behaves. It is not a security specification for
  the application being built, and application-specific requirements do not
  belong in it.

Use specification-driven development for every change that could alter how an
assistant behaves. Read [`specs/README.md`](specs/README.md) before changing the
baseline, a test case, or the workflow—it describes how changes run here.

Two rules hold no matter how small the change looks:

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
  permission prompt for tools that support hooks; merge
  `scripts/spec-guard.settings.json` into `.claude/settings.json` to install it.

Run `make check` after changing the baseline, the specs, test metadata, or the
harness. It calls no model, takes seconds, and also holds this file to its own
contract: `AGENTS.md` must require agents to read and follow the baseline
through the reference above, must not carry a generated copy of it, and
`CLAUDE.md` must import both files exactly once.

`make test` and `make test-all` are a different matter: they run the cases
against real models. The full matrix is 60 runs and several hours of tokens.
Run them when the user asks, or for the cases a change affects — never as a
routine check. They are evidence, not a gate.
