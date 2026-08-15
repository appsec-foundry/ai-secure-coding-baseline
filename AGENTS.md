# Repository instructions

This repository publishes `secure-coding-baseline.md`. That file is the product:
the rules an assistant follows. Everything else exists to keep it correct.

Read `specs/README.md` before changing the baseline, a test case, or the
workflow — it describes how changes run here. When you change code or
configuration in this repository, follow the baseline itself.

Two rules hold no matter how small the change looks:

- Requirements come only from an explicit user request, existing repository
  documentation, or commit history that clearly establishes the behavior. Name
  the source. If none of them settles a question, ask instead of deciding it.
- Normative rule text lives in `secure-coding-baseline.md`. The requirements
  catalog may explain it, but must not add or change behavior.

Run `make check` after changing the baseline, the specs, test metadata, or the
harness.
