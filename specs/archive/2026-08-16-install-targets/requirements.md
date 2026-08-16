# Requirements

## INSTALL-001 One target per tool

Source: the user's explicit request in this conversation for `make
install-claude`, `make install-codex`, and the like, together with the
installation locations `README.md` already documents.

The repository must provide `make install-claude`, `make install-codex`, and
`make install-copilot`, each linking `secure-coding-baseline.md` into that
tool's instruction location, and `make install`, which does the same for every
tool whose location is present.

Acceptance: each target creates the documented link and reports what it did; a
tool is added by a single table entry naming its name, path, and mechanism.

## INSTALL-002 Link, never overwrite

Source: the user's explicit request in this conversation for symlinks rather
than copies, and `README.md`, which keeps one real file because every copy is a
chance to drift.

The installer must create symbolic links, must not write over an existing file,
and must instead report the manual step that would be needed — appending, where
an `AGENTS.md` already carries other instructions. Running it twice must change
nothing.

Acceptance: an existing target file is left byte-identical and the required
step is printed; a second run reports the link as already in place.

## INSTALL-003 Project by default, machine on request

Source: the user's explicit request in this conversation for a project default
with a machine-wide option, and the per-scope locations in `README.md`.

The installer must default to the current project and take an option that
selects the machine-wide locations instead.

Acceptance: without the option the links land in the project; with it they land
in the tool's user-level directory.
