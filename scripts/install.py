#!/usr/bin/env python3
"""Link the baseline into the places coding agents read.

Every tool loads instructions from its own fixed location, so installing means
putting the file where the tool already looks. One real file, symlinks pointing
at it: a copy is only made when the baseline is not in the target project yet,
and nothing that already exists is ever written over.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = "secure-coding-baseline.md"
SOURCE = REPO / BASELINE

# A tool is one row: where it reads, and how. `link` is a symlink the tool
# loads on its own; `import_line` is a line a Claude instruction file needs.
# Adding a tool means adding a row, nothing else.
TOOLS = ("claude", "codex", "copilot")


def project_targets(root: Path) -> dict[str, list[tuple[str, Path]]]:
    return {
        "claude": [("link", root / ".claude" / "rules" / BASELINE)],
        "codex": [("link", root / "AGENTS.md")],
        "copilot": [("link", root / ".github" / "copilot-instructions.md")],
    }


def user_targets(home: Path) -> dict[str, list[tuple[str, Path]]]:
    return {
        "claude": [("link", home / ".claude" / BASELINE),
                   ("import_line", home / ".claude" / "CLAUDE.md")],
        "codex": [("link", home / ".codex" / "AGENTS.md")],
        "copilot": [],
    }


def link_text(target: Path, source: Path, *, relative: bool) -> str:
    """Inside a project the link stays relative, so a clone keeps working."""
    return os.path.relpath(source, target.parent) if relative else str(source)


def place_baseline(root: Path, report: list[str]) -> Path | None:
    """The project needs the real file before anything can point at it."""
    local = root / BASELINE
    if local.resolve() == SOURCE.resolve():
        return local
    if not local.exists():
        shutil.copy(SOURCE, local)
        report.append(f"added {local}")
    return local


def install_link(target: Path, source: Path, report: list[str],
                 *, relative: bool) -> None:
    link = link_text(target, source, relative=relative)
    if target.is_symlink():
        if Path(os.readlink(target)) == Path(link):
            report.append(f"in place {target}")
            return
        report.append(f"blocked {target}: points elsewhere, remove it first")
        return
    if target.exists():
        report.append(f"blocked {target}: exists — append "
                      f"{source.name} to it by hand")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(link)
    report.append(f"linked {target} -> {link}")


def install_import_line(target: Path, source: Path, report: list[str]) -> None:
    line = f"@{source}"
    if target.exists():
        if line in target.read_text(encoding="utf-8").splitlines():
            report.append(f"in place {target}")
        else:
            report.append(f"blocked {target}: exists — add the line {line!r} by hand")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"{line}\n", encoding="utf-8")
    report.append(f"wrote {target}")


def install(tools: list[str], root: Path, home: Path | None) -> list[str]:
    report: list[str] = []
    if home is not None:
        targets, source = user_targets(home), SOURCE
    else:
        targets = project_targets(root)
        source = place_baseline(root, report)

    for tool in tools:
        actions = targets[tool]
        if not actions:
            report.append(f"skipped {tool}: no documented location for this scope")
            continue
        for kind, target in actions:
            if kind == "link":
                install_link(target, source, report, relative=home is None)
            else:
                install_import_line(target, source, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # argparse rejects its own empty default when choices are set, so the
    # names are checked here instead.
    parser.add_argument("tools", nargs="*",
                        help=f"any of {', '.join(TOOLS)}; default is all of them")
    parser.add_argument("--user", action="store_true",
                        help="install for this machine instead of the project")
    parser.add_argument("--into", type=Path, default=Path.cwd(),
                        help="project directory (default: the current one)")
    args = parser.parse_args(argv)

    tools = list(args.tools) or list(TOOLS)
    unknown = [tool for tool in tools if tool not in TOOLS]
    if unknown:
        parser.error(f"unknown tool {unknown[0]!r}; choose from {', '.join(TOOLS)}")
    home = Path.home() if args.user else None
    for line in install(tools, args.into.resolve(), home):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
