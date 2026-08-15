# Repository instructions

This repository publishes `secure-coding-baseline.md`. That file is the product:
the rules an assistant follows. Everything else exists to keep it correct.

Before doing any repository work, read and follow
[`secure-coding-baseline.md`](secure-coding-baseline.md); it is the normative
source for assistant behavior.

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

Run `make check` after changing the baseline, the specs, test metadata, or the
harness.
