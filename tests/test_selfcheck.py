#!/usr/bin/env python3
"""Check that selfcheck.py still fails when something is actually wrong.

selfcheck.py is the only thing standing between a broken suite and a paid model
run, and a guard nobody tests is a guard that can quietly stop guarding. Each
case below breaks a tiny throwaway repository in one realistic way and expects
the message that should come out.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

BASELINE = """\
# Demo baseline

## Non-negotiable

- **[AISEC-DEMO-001] First rule:** Do the safe thing.
- **[AISEC-DEMO-002] Second rule:** Do it again.
"""

CATALOG = """\
# Secure coding requirements catalog

## AISEC-DEMO-001 — First rule

**Section:** Non-negotiable
**Normative source:** `secure-coding-baseline.md`, rule group `AISEC-DEMO-001`.
**Applies when:** The demo runs.
**Requirement:** Do the safe thing.
**Observable acceptance:** The result is safe.
**Model cases:** `demo-case`
**Evidence and gaps:** Partial. One demo case covers it.

## AISEC-DEMO-002 — Second rule

**Section:** Non-negotiable
**Normative source:** `secure-coding-baseline.md`, rule group `AISEC-DEMO-002`.
**Applies when:** The demo runs again.
**Requirement:** Repeat the safe action.
**Observable acceptance:** The result is safe again.
**Model cases:** None.
**Evidence and gaps:** None. No model case declares it.
"""

CHECKS = """\
{
  "mode": "greenfield",
  "why": "A minimal valid case for guard tests.",
  "requirements": ["AISEC-DEMO-001"],
  "reply_required_regex": [{"id": "says-something", "pattern": "safe"}]
}
"""

PROPOSAL = """\
# Demo change

## Problem
The old behavior is unclear.

## Goal
Make it clear.

## Non-goals
Do not change unrelated behavior.

## Compatibility
Existing callers remain supported.
"""

CHANGE_REQUIREMENTS = """\
# Requirements

## DEMO-001 Clear behavior

Source: the explicit demo request.

The system must make the behavior clear.

Acceptance: the resulting behavior is unambiguous.
"""

AGENTS = """\
# Repository instructions

Before doing any repository work, read and follow
[`secure-coding-baseline.md`](secure-coding-baseline.md); it is normative.
"""


def build(root: Path) -> None:
    """A miniature of this repository: baseline, catalog, one case, the guard."""
    (root / "specs").mkdir()
    (root / "tests" / "cases" / "demo-case").mkdir(parents=True)
    (root / "secure-coding-baseline.md").write_text(BASELINE)
    (root / "AGENTS.md").write_text(AGENTS)
    (root / "CLAUDE.md").write_text("@AGENTS.md\n@secure-coding-baseline.md\n")
    (root / "specs" / "requirements.md").write_text(CATALOG)
    (root / "tests" / "cases" / "demo-case" / "prompt.md").write_text("do the thing\n")
    (root / "tests" / "cases" / "demo-case" / "checks.json").write_text(CHECKS)
    # selfcheck compiles run.py; the real one is irrelevant to these guards.
    (root / "tests" / "run.py").write_text("# stub\n")
    shutil.copy(HERE / "selfcheck.py", root / "tests" / "selfcheck.py")


def edit(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text().replace(old, new))


def make_change(directory: Path, *, completed: bool = True) -> None:
    directory.mkdir(parents=True)
    (directory / "proposal.md").write_text(PROPOSAL)
    (directory / "requirements.md").write_text(CHANGE_REQUIREMENTS)
    mark = "x" if completed else " "
    (directory / "tasks.md").write_text(f"# Tasks\n\n- [{mark}] Finish the change.\n")


def add_failing_precondition(root: Path) -> None:
    case = root / "tests" / "cases" / "demo-case"
    (case / "fixture").mkdir()
    edit(case / "checks.json", '\n}',
         ',\n  "fixture_precondition": {"cmd": "true", "expect_exit": 1}\n}')


# Each case gets the throwaway repository and breaks it. The second value is
# what selfcheck must say; None means it must stay silent and pass.
CASES = [
    ("intact repository", lambda r: None, None),
    ("agent baseline reference is missing",
     lambda r: (r / "AGENTS.md").write_text("# Repository instructions\n"),
     "AGENTS.md must require agents to read and follow"),
    ("generated agent baseline block is reintroduced",
     lambda r: edit(r / "AGENTS.md", "# Repository instructions",
                    "# Repository instructions\n\n"
                    "<!-- BEGIN GENERATED SECURE CODING BASELINE -->"),
     "AGENTS.md must reference secure-coding-baseline.md instead of embedding"),
    ("Claude baseline import is missing",
     lambda r: edit(r / "CLAUDE.md", "@secure-coding-baseline.md\n", ""),
     "CLAUDE.md must import secure-coding-baseline.md exactly once"),
    ("rule group renamed in the baseline",
     lambda r: edit(r / "secure-coding-baseline.md", "First rule", "Renamed rule"),
     "catalog calls AISEC-DEMO-001"),
    ("rule group added without a catalog entry",
     lambda r: edit(r / "secure-coding-baseline.md", "\n## Non",
                    "\n- **[AISEC-DEMO-003] Third rule:** New.\n\n## Non"),
     "catalog does not list 'AISEC-DEMO-003'"),
    ("case coverage the catalog does not show",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '["AISEC-DEMO-001"]', '["AISEC-DEMO-001", "AISEC-DEMO-002"]'),
     "catalog cases for AISEC-DEMO-002"),
    ("case pointing at an id that does not exist",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    "AISEC-DEMO-001", "AISEC-GONE-001"),
     "unknown requirement id"),
    ("duplicate id in the baseline",
     lambda r: edit(r / "secure-coding-baseline.md", "AISEC-DEMO-002", "AISEC-DEMO-001"),
     "duplicate requirement id"),
    ("malformed id in the baseline",
     lambda r: edit(r / "secure-coding-baseline.md", "AISEC-DEMO-002", "AISEC-demo-002"),
     "malformed requirement id"),
    ("rule group without an id",
     lambda r: edit(r / "secure-coding-baseline.md",
                    "- **[AISEC-DEMO-002] Second rule:**",
                    "- **Second rule:**"),
     "has no valid requirement id"),
    ("catalog entry missing its requirement text",
     lambda r: edit(r / "specs" / "requirements.md",
                    "**Requirement:** Do the safe thing.",
                    "**Summary:** Do the safe thing."),
     "is missing 'Requirement'"),
    ("misspelled key in checks.json",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '"mode"', '"moed"'),
     "unknown key"),
    ("check pattern that does not compile",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '"safe"', '"safe("'),
     "does not compile"),
    ("case with no observable checks",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '[{"id": "says-something", "pattern": "safe"}]', '[]'),
     "no checks at all"),
    ("fixture no longer has its required starting state",
     add_failing_precondition,
     "fixture_precondition 'true' exited 0, expected 1"),
    ("change directory missing a file",
     lambda r: (r / "specs" / "changes" / "half-done").mkdir(parents=True),
     "half-done is missing proposal.md"),
    ("change proposal missing meaningful content",
     lambda r: (make_change(r / "specs" / "changes" / "empty-goal"),
                edit(r / "specs" / "changes" / "empty-goal" / "proposal.md",
                     "## Goal\nMake it clear.", "## Goal")),
     "missing a non-empty 'Goal' section"),
    ("change requirement missing its source",
     lambda r: (make_change(r / "specs" / "changes" / "no-source"),
                edit(r / "specs" / "changes" / "no-source" / "requirements.md",
                     "Source:", "Origin:")),
     "requirement DEMO-001 has no source"),
    ("change requirement missing acceptance",
     lambda r: (make_change(r / "specs" / "changes" / "no-acceptance"),
                edit(r / "specs" / "changes" / "no-acceptance" / "requirements.md",
                     "Acceptance:", "Result:")),
     "requirement DEMO-001 has no acceptance criterion"),
    ("change requirement id repeated",
     lambda r: (make_change(r / "specs" / "changes" / "duplicate-requirement"),
                edit(r / "specs" / "changes" / "duplicate-requirement" /
                     "requirements.md", "## DEMO-001 Clear behavior",
                     "## DEMO-001 Clear behavior\n\nSource: the explicit demo request.\n\n"
                     "The first copy must be clear.\n\nAcceptance: the first copy is clear.\n\n"
                     "## DEMO-001 Clear behavior")),
     "repeats 'DEMO-001'"),
    ("archived change has unfinished work",
     lambda r: make_change(r / "specs" / "archive" / "2026-08-15-unfinished",
                           completed=False),
     "has unfinished tasks in the archive"),
    ("archived change without a valid date in its name",
     lambda r: make_change(r / "specs" / "archive" / "no-date"),
     "no-date should start with a valid date"),
]


def main() -> int:
    failures = 0
    for name, break_it, expected in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build(root)
            break_it(root)
            proc = subprocess.run([sys.executable, str(root / "tests" / "selfcheck.py")],
                                  capture_output=True, text=True)
            output = proc.stdout + proc.stderr
            if expected is None:
                ok = proc.returncode == 0
                complaint = f"expected a clean pass, got:\n{output}"
            else:
                ok = proc.returncode == 1 and expected in output
                complaint = f"expected a failure mentioning {expected!r}, got:\n{output}"
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures += 1
            print(f"     {complaint}")

    print(f"\n{len(CASES)} guards checked, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
