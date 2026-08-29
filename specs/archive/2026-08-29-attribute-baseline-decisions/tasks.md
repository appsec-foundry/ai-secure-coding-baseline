# Tasks

- [x] Add baseline attribution and timing as an Operating Mode rule, add the
      browser Basic authentication best-practice trigger, and bump the baseline
      to `aisec-0.1.10`.
- [x] Update the affected model cases and their requirement IDs. Add
      `design-browser-basic-auth` for the reported Flask browser-login design.
- [x] Update `specs/requirements.md` and the README. The baseline measures
      20,118 bytes and 3,998 `o200k_base` tokens.
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not. A one-repeat, no-judge
      smoke run of all five affected cases produced three 360-second
      `INCOMPLETE` runs before being stopped; a direct-service rerun of
      `design-browser-basic-auth` also produced no result after ten minutes.
      These environment or agent timeouts provide no model evidence.
- [x] Review the diff and archive this directory. The new tests add checks and
      do not skip or weaken existing behavior; no application route, listener,
      credential literal, dependency, build command, or deployment path is
      added by this documentation and harness change.
