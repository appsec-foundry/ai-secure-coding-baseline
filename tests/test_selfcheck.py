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

INDEX = """\
# Rule groups and their tests

| ID | Rule group | Section | Covered by cases |
|---|---|---|---|
| `AISEC-DEMO-001` | First rule | Non-negotiable | `demo-case` |
| `AISEC-DEMO-002` | Second rule | Non-negotiable | – |
"""

CHECKS = """\
{
  "mode": "greenfield",
  "requirements": ["AISEC-DEMO-001"],
  "reply_required_regex": [{"id": "says-something", "pattern": "safe"}]
}
"""


def build(root: Path) -> None:
    """A miniature of this repository: baseline, index, one case, the guard."""
    (root / "specs").mkdir()
    (root / "tests" / "cases" / "demo-case").mkdir(parents=True)
    (root / "secure-coding-baseline.md").write_text(BASELINE)
    (root / "specs" / "requirements.md").write_text(INDEX)
    (root / "tests" / "cases" / "demo-case" / "prompt.md").write_text("do the thing\n")
    (root / "tests" / "cases" / "demo-case" / "checks.json").write_text(CHECKS)
    # selfcheck compiles run.py; the real one is irrelevant to these guards.
    (root / "tests" / "run.py").write_text("# stub\n")
    shutil.copy(HERE / "selfcheck.py", root / "tests" / "selfcheck.py")


def edit(path: Path, old: str, new: str) -> None:
    path.write_text(path.read_text().replace(old, new))


def make_change(directory: Path) -> None:
    directory.mkdir(parents=True)
    for name in ("proposal.md", "requirements.md", "tasks.md"):
        (directory / name).write_text("# stub\n")


# Each case gets the throwaway repository and breaks it. The second value is
# what selfcheck must say; None means it must stay silent and pass.
CASES = [
    ("intact repository", lambda r: None, None),
    ("rule group renamed in the baseline",
     lambda r: edit(r / "secure-coding-baseline.md", "First rule", "Renamed rule"),
     "index calls AISEC-DEMO-001"),
    ("rule group added without an index entry",
     lambda r: edit(r / "secure-coding-baseline.md", "\n## Non",
                    "\n- **[AISEC-DEMO-003] Third rule:** New.\n\n## Non"),
     "index does not list 'AISEC-DEMO-003'"),
    ("case coverage the index does not show",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '["AISEC-DEMO-001"]', '["AISEC-DEMO-001", "AISEC-DEMO-002"]'),
     "index coverage for AISEC-DEMO-002"),
    ("case pointing at an id that does not exist",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    "AISEC-DEMO-001", "AISEC-GONE-001"),
     "unknown requirement id"),
    ("duplicate id in the baseline",
     lambda r: edit(r / "secure-coding-baseline.md", "AISEC-DEMO-002", "AISEC-DEMO-001"),
     "duplicate requirement id"),
    ("misspelled key in checks.json",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '"mode"', '"moed"'),
     "unknown key"),
    ("check pattern that does not compile",
     lambda r: edit(r / "tests" / "cases" / "demo-case" / "checks.json",
                    '"safe"', '"safe("'),
     "does not compile"),
    ("change directory missing a file",
     lambda r: (r / "specs" / "changes" / "half-done").mkdir(parents=True),
     "half-done is missing proposal.md"),
    ("archived change without a date in its name",
     lambda r: make_change(r / "specs" / "archive" / "no-date"),
     "no-date should start with a date"),
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
