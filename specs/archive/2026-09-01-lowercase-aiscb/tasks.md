# Tasks

- [x] Change the baseline without changing its version or rule behavior.
- [x] Update the test cases, harness, and their requirement IDs.
- [x] Update `specs/requirements.md` and the documentation.
- [x] Recompute the baseline size and `o200k_base` token count in `README.md`.
- [x] Create immutable bundle tag `aiscb-bundle-0.1.10-2`, pin its hashes in
      `setup.sh`, and update the complete Quick start through the required
      follow-up commit.
- [x] Run `make check`.
- [x] Attempt the five affected model cases. Not run: both the Claude and Codex
      matrices stopped at preflight because their baseline arms reported no
      loaded baseline; the harness correctly refused to compare two control
      arms, and no case runs were started.
- [x] Review the diff for introduced security findings.
- [x] Archive this directory.
