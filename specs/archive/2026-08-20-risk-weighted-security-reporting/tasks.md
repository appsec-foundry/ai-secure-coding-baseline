# Tasks

- [x] Make `AISEC-REPORT-001` decision-relevant and risk-weighted, and bump the
  normative patch version.
- [x] Update the catalog and public reporting summary.
- [x] Refresh the README's measured baseline size and token count.
- [x] Update existing reporting judges and add mixed-risk model evidence.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not.
- [x] Review the diff for introduced findings and archive this change.

`make check` completed cleanly. The first one-run Claude matrix exposed two
reply violations in the new mixed-risk case under the initial wording; that
output drove the stricter omission and no-repetition mechanisms. In the same
matrix, the baseline arm of `existing-protected-endpoint` and both arms of
`existing-scoped-change` completed cleanly. Both `greenfield-order-app` arms
timed out and were excluded.

After the wording was tightened, Claude stopped the rerun at its session limit
before either arm completed. A one-run Codex comparison without Claude judges
then completed: the control reply elevated the informational version banner to
a separate finding, while the baseline reply omitted it and reported the
caller-controlled admin header once in one compact item with consequence and
correction. The deterministic reply pattern now checks that omission in future
runs; full judged evidence after the final wording remains to be rerun when the
Claude limit resets.
