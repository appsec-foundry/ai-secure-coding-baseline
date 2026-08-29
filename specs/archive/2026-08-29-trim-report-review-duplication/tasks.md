# Tasks

- [x] Change the first sub-bullet of `AISEC-REPORT-001`: add binds to the
      reachable surfaces, drop the repeating application-or-service sentence,
      and bump the baseline to `aisec-0.1.9`. The sub-bullet goes from 76 to 61
      words, the baseline from 3,899 to 3,883 `o200k_base` tokens.
- [x] Update the test cases and their requirement IDs. None needed: no case
      observed the removed sentence, and the reachability check the first
      sentence keeps is already exercised by `existing-protected-endpoint`,
      `existing-scoped-change`, `greenfield-order-app`, and
      `greenfield-web-api-hardening`.
- [x] Update `specs/requirements.md` and the documentation. The catalog entry
      summarizes the duty as "newly reachable surfaces" and never carried the
      removed sentence, so it stays as it is; the README carries the new version
      and the new size.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not. Not run: the user chose the
      no-run option when the change was proposed. The cases to run when evidence
      is wanted are the four named above; the change removes a review duty that
      none of them observes and widens the remaining one from applications and
      services to every change.
- [x] Archive this directory.
