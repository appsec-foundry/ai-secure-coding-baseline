# Tasks

- [x] Point `AISEC-OM-002` at the security note and bump the baseline to
      `aisec-0.1.5`.
- [x] Update the test cases and their requirement IDs. None needed:
      `override-demo-app` and `design-riskier-choice` judge a verdict on
      production use as a statement, not as a named note part, and
      `AISEC-REPORT-001` still governs when that statement appears.
- [x] Update `specs/requirements.md` and the documentation. `AISEC-OM-004` and
      `AISEC-OM-005` acceptance now name the security note like the baseline;
      the two evidence lines keep the case wording. `AISEC-REPORT-001`
      acceptance dropped the enumeration of forbidden note contents, which
      described output format rather than observable behavior, and went from
      105 words to 56 against a catalog median of 17.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not. Not run: the change removes
      a dangling reference and adds no behavior; `override-demo-app` is the case
      to run when evidence is wanted.
- [x] Archive this directory.
