# Tasks

- [x] Point the reporting duty in `AISEC-OM-001` at the threshold in Review and
      Report (`SCOPE-001`).
- [x] Rewrite the reporting bullets of `AISEC-REPORT-001`: security relevance
      before materiality, the pre-existing case stated once, prohibitions folded
      into general statements (`SCOPE-002`, `SCOPE-003`). The group holds 3,702
      `o200k_base` tokens before and after the change and is 66 bytes shorter.
- [x] Bump the baseline to `aisec-0.1.6`.
- [x] Update `specs/requirements.md` for both rule groups and check the test
      cases the change affects. No case changed. `existing-scoped-change` reports
      the md5 hashing in `auth.js`, which the new endpoint relies on through the
      existing authentication, and `existing-risk-weighted-report` is a
      read-only review the user asked for; the threshold covers both, and the
      review scope was added to the rule text for that reason.
- [x] Update `README.md`: version references and the size figures.
- [x] Run `make check`.
- [ ] Run the affected model cases, or note why not.
- [ ] Archive this directory.
