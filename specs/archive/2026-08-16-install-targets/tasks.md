# Tasks

- [x] Write `scripts/install.py` with the tool table, link creation, and the
      no-overwrite report.
- [x] Add the `install`, `install-claude`, `install-codex`, and
      `install-copilot` targets.
- [x] Add `scripts/test_install.py` and run it from `make check`.
- [x] Point the README's installation section at the targets.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not.
- [x] Archive this directory.

No model case is affected: the installer changes where the baseline is placed,
not what it says. Its behavior is covered by `scripts/test_install.py`.

Grok has no row yet. Its instruction location was not confirmed against current
documentation, and an unverified path would install the baseline where nothing
reads it.
