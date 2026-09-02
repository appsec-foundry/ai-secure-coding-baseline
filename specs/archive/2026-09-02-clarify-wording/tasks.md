# Tasks

- [x] Change the baseline without changing its version.
- [x] Update the test cases and their requirement IDs: no case names a changed
      phrase and no requirement ID changed, so nothing to update.
- [x] Update `specs/requirements.md` and the documentation, including the
      baseline size and `o200k_base` token count in `README.md`.
- [x] Ship in bundle tag `aiscb-bundle-0.1.10-3` together with
      `clarify-security-note-scope`.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not. Not run: the change
      removes unintended readings without adding a rule, and a matrix run
      costs hours of tokens for stochastic evidence; the affected cases stay
      listed in the catalog for the next scheduled run.
- [x] Archive this directory.
