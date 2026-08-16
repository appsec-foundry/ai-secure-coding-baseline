#!/usr/bin/env python3
"""Check that install.py links where it should and leaves everything else alone.

An installer that quietly overwrites a project's own AGENTS.md destroys work
that is not its own, and one that is not idempotent cannot be run twice. Both
are checked here against a throwaway directory.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install  # noqa: E402

failures = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global failures
    print(f"{'ok  ' if condition else 'FAIL'} {name}")
    if not condition:
        failures += 1
        if detail:
            print(f"     {detail}")


def run(root: Path, *tools: str) -> list[str]:
    return install.install(list(tools) or list(install.TOOLS), root, None)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    report = run(root)

    baseline = root / install.BASELINE
    check("the project gets the real baseline", baseline.is_file())
    check("Claude reads it from .claude/rules",
          (root / ".claude" / "rules" / install.BASELINE).is_symlink())
    check("the AGENTS.md tools read it from the root",
          (root / "AGENTS.md").is_symlink())
    check("Copilot reads it from .github",
          (root / ".github" / "copilot-instructions.md").is_symlink())
    check("links resolve to the project's own file",
          (root / "AGENTS.md").resolve() == baseline.resolve())
    check("links stay relative, so a clone keeps working",
          not Path((root / "AGENTS.md").readlink()).is_absolute(),
          str((root / "AGENTS.md").readlink()))
    check("every step is reported", len(report) >= 4, str(report))

    again = run(root)
    check("a second run changes nothing",
          all(line.startswith("in place") for line in again), str(again))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    own = root / "AGENTS.md"
    own.write_text("# our own instructions\n")
    report = run(root, "codex")

    check("an existing AGENTS.md survives untouched",
          own.read_text() == "# our own instructions\n")
    check("and the manual step is named",
          any("append" in line for line in report), str(report))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    stale = root / "AGENTS.md"
    stale.symlink_to("somewhere-else.md")
    report = run(root, "codex")
    check("a foreign symlink is refused, not replaced",
          stale.readlink() == Path("somewhere-else.md")
          and any("points elsewhere" in line for line in report), str(report))

print(f"\ninstall: {'ok' if not failures else f'{failures} failures'}")
sys.exit(1 if failures else 0)
