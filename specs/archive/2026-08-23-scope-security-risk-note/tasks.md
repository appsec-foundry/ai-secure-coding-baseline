# Tasks

- [x] Point the reporting duty in `AISEC-OM-001` at the threshold in Review and
      Report (`SCOPE-001`).
- [x] Rewrite the reporting bullets of `AISEC-REPORT-001`: security relevance
      before materiality, the pre-existing case stated once, prohibitions folded
      into general statements (`SCOPE-002`, `SCOPE-003`). That initial rewrite
      held 3,702 `o200k_base` tokens before the later requirements were added.
- [x] Bind the residual-risk note to a qualifying adverse security change in the
      delivered state (`SCOPE-004`).
- [x] Make ordinary verification status insufficient to trigger the note
      (`SCOPE-005`).
- [x] Attribute a baseline-added note without duplicating explicit risk reviews
      (`SCOPE-006`).
- [x] Bump the baseline to `aisec-0.1.7`.
- [x] Update `specs/requirements.md` and the affected cases. Add
      `existing-targeted-verification` for the reported false positive and
      `design-accepted-risk-note` for isolated title evidence; add the exact
      title to the accepted prototype trade-off and scope its non-loopback regex
      so a negative test input is not mistaken for a listener.
- [x] Update `README.md`: version references, reporting summary, and the final
      19.0 KB / 3,772-token size figures.
- [x] Run `make check`.
- [x] Run the affected model cases. `existing-targeted-verification` had zero
      findings in both arms; `existing-preserve-only-change` had zero in both;
      and `existing-protected-endpoint` had zero in the baseline arm versus one
      control validation finding. The rerun of `existing-risk-weighted-report`
      removed the informational version finding in the baseline arm, while two
      unrelated brevity/filler judgments remained. The large prototype title
      case first missed the title; after the exact cross-references were added,
      its rerun and the isolated design-title rerun both hung in the outer tool
      execution layer without a runner result and were terminated. Reports:
      `20260823T115013Z`, `20260823T115252Z`, `20260823T120046Z`.
- [x] Archive this directory.
