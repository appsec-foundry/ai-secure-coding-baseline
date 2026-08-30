# Rename the rule prefix to AISCB and name the baseline's source

## Problem

Two problems meet in the same two lines of the baseline.

`AISEC` reads as "AI security", the securing of AI systems. This file is
secure-coding guidance for assistants that write code, so the acronym points at
the wrong field. The repository is now `appsec-foundry/aiscb`, which leaves the
prefix, the repository, and the risk heading assistants print saying three
different things.

The file is also built to be copied. The installer places it in home
directories and projects, and organizations run derived versions. No copy says
where it came from or that it is CC BY 4.0, so a recipient who finds it in a
repository cannot give the attribution the license asks of them.

## Goal

One acronym for the rule set, `AISCB`, in the baseline, the catalog, the
documentation, the test cases, and the installer's official-name check. One
metadata line in the baseline that names source and license.

## Non-goals

No rule changes: every group keeps its behavior, its group name, and its
number. No update instruction, install command, or version check in the rule
text. No change to the file name `secure-coding-baseline.md` or to the on-disk
installation paths, which are installation state rather than repository
identity.

## Compatibility

The `baseline-id` prefix changes, and `OFFICIAL_NAME` in the installer changes
with it, so a file carrying the old prefix counts as a customized baseline and
is no longer updated in place. The published release `aisec-0.1.9` fails the
official-name check in `fetch_release_baseline`, which makes the online check
fall back to the bundled copy until a release carrying the new prefix exists.
Publishing that release is part of this change.
