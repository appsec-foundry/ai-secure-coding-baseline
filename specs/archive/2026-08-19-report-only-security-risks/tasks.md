# Tasks

- [x] Make the security note risk-only and remove the mandatory four parts.
- [x] Align operating-mode references and bump the baseline to `aisec-0.1.1`.
- [x] Add a model case for a fully protected security change with no note.
- [x] Update `greenfield-order-app` to reject non-risk assurance output.
- [x] Update `specs/requirements.md` and the documentation.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not.
- [x] Archive this directory.

One comparison run per arm completed cleanly for
`existing-preserve-only-change` and `existing-protected-endpoint`, including
the endpoint's executable tests and reply judges. Both `greenfield-order-app`
runs were excluded after the Claude CLI reached its weekly limit; rerun that
case after the quota resets.
