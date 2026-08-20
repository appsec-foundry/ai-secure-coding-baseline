# Tasks

- [x] Change `AISEC-REPORT-001` so the default risk item names scope,
      consequence, and the next action or accepted status, and bump the baseline
      to `aisec-0.1.4`.
- [x] Update the test cases and their requirement IDs. None needed:
      `existing-risk-weighted-report` already judges a reply that "gives no
      concrete safe direction", which is the behavior this change restores.
- [x] Update `specs/requirements.md` and the documentation. The catalog entry
      already calls a reported risk actionable and already scales detail to what
      the corrective action needs, so it stays as it is; the README carries the
      new version.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not. Not run: the user asked for
      the fix and the commit, and a run costs tokens without being a gate.
      `existing-risk-weighted-report` is the case to run when evidence is wanted.
- [x] Archive this directory.
