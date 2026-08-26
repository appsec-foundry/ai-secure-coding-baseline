# Tasks

- [x] Change `AISEC-LLM-001` and set the approved baseline ID to `aisec-0.1.8`.
- [x] Add the LLM output-validation model case and its requirement ID.
- [x] Make the runner preserve NUL-containing source tests and recognize the Claude weekly-limit response.
- [x] Update `specs/requirements.md`, `README.md`, and `tests/README.md`.
- [x] Run `make check`.
- [x] Run the affected model case, or note why not. The Claude matrix could not
  complete because the account reached its weekly limit. A one-repeat Codex
  A/B run without the unavailable Claude judge completed as partial evidence;
  after review, its lone deterministic finding was removed as a regex false
  positive on JavaScript `RegExp.exec`.
- [x] Review the diff for credentials and newly reachable interfaces.
- [x] Archive this directory.
