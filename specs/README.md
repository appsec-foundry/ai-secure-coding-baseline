# How the baseline changes

`secure-coding-baseline.md` in the repository root is the product — one file,
shipped to coding assistants as it is. Nothing under `specs/` is normative for
an assistant; it only records what the baseline contains and how it changes.

- `requirements.md` — the rule groups that exist today and the cases covering them.
- `changes/<name>/` — a change being worked on.
- `archive/<date>-<name>/` — a change that is finished.

## Where requirements come from

Three sources, and no fourth: what the user asked for, what this repository
already documents, or a commit that clearly established the behavior. Name the
source for each requirement.

If none of them settles a question, ask. Do not fill the gap with a rule, an
exception, a test obligation, or a scope extension of your own. An example may
make a sourced rule easier to see; it must not add to it.

## When a change needs its own directory

Whenever it could change how an assistant behaves. Typos, rewrapping, and edits
to files like this one do not. If you cannot tell whether new wording changes
behavior, assume it does.

A change directory holds three short files — templates in `changes/README.md`:

- `proposal.md` — problem, goal, non-goals, what it breaks.
- `requirements.md` — what the baseline must do, with a source per requirement.
- `tasks.md` — the work, ticked off as it happens.

## Running a change

1. Write the three files.
2. Change the baseline, the test cases, and the documentation.
3. Run `make check`.
4. Run the model cases the change affects, or note in `tasks.md` why you did
   not. They are evidence, not a gate: they cost money and vary between runs.
5. Move the directory to `archive/<date>-<short-name>/`.

## Requirement IDs

Every rule group in the baseline carries an ID like `AISEC-AUTH-001`. The ID
belongs to the behavior, not to the heading or the line: reword the rule and it
keeps its ID. Split a group and the new half gets a new ID. Remove a group and
its ID retires — never reuse it.

Test cases name the IDs they exercise in their `checks.json`. A rule group
without a case is not automatically a gap, and not automatically fine. Add a
case relationship only when the case really observes that behavior.

## What is enforced

`make check` runs on every push and pull request
(`.github/workflows/check.yml`), takes about a second, and never calls a model.
It fails on:

- an ID that is duplicated, malformed, or not attached to a rule group;
- a case naming an ID the baseline does not define;
- a row in `requirements.md` that no longer matches the baseline or the cases;
- a change directory missing one of its three files, or an archived one whose
  name does not start with a date;
- a case with an unknown key, a pattern that does not compile, or no checks;
- a fixture that no longer starts in the state its case depends on.

`tests/test_selfcheck.py` breaks a throwaway repository in each of those ways
and expects the complaint, so the check itself cannot rot unnoticed.

Nothing here can tell whether a requirement really came from the source it
names, or whether the rule is any good. That needs a reader. Whether an
assistant actually follows it needs a model run.
