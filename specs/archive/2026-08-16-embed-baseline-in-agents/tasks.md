# Tasks

- [x] Restore `scripts/sync_agents.py` and the `make sync-agents` target.
- [x] Embed the generated baseline block in `AGENTS.md`.
- [x] Reduce `CLAUDE.md` to the `AGENTS.md` import.
- [x] Replace the reference checks in `tests/selfcheck.py` with drift checks and
      update `tests/test_selfcheck.py`.
- [x] Update `README.md` and `specs/README.md`.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not.
- [x] Archive this directory.

No model case is affected: this change moves no rule text. What it changes is
whether an assistant receives the rules at all, which the cases cannot observe —
they install the baseline themselves. The check for it is `baseline?` in a tool
that reads `AGENTS.md` and resolves no references.
