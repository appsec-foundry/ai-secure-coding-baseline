# Tasks

- [x] Add the approved rule and rule extensions to the baseline and bump it to `aisec-0.1.3`.
- [x] Add or update the affected model cases and their requirement IDs.
- [x] Update `specs/requirements.md` and the README, including the measured baseline size and token count.
- [x] Run `make check`.
- [x] Attempt the affected `existing-retrieved-instructions` model case; the Claude session limit stopped the run before any of the six jobs, so no live-model result is available. `make check` validates its structure and failing fixture precondition.
- [x] Review the diff for credential literals and newly reachable interfaces.
- [x] Archive this directory.
