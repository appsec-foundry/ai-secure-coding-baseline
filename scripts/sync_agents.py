#!/usr/bin/env python3
"""Refresh the baseline embedded in the root AGENTS.md."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "AGENTS.md"
BASELINE = ROOT / "secure-coding-baseline.md"
BEGIN = "<!-- BEGIN GENERATED SECURE CODING BASELINE -->"
END = "<!-- END GENERATED SECURE CODING BASELINE -->"


def main() -> int:
    agents = AGENTS.read_text(encoding="utf-8")
    if agents.count(BEGIN) != 1 or agents.count(END) != 1:
        raise SystemExit("AGENTS.md must contain exactly one generated baseline block")
    prefix, generated = agents.split(BEGIN, 1)
    _, suffix = generated.split(END, 1)
    if suffix.strip():
        raise SystemExit("the generated baseline block must be last in AGENTS.md")

    baseline = BASELINE.read_text(encoding="utf-8").rstrip("\n")
    updated = f"{prefix.rstrip()}\n\n{BEGIN}\n\n{baseline}\n\n{END}\n"
    if updated != agents:
        AGENTS.write_text(updated, encoding="utf-8")
        print("updated AGENTS.md")
    else:
        print("AGENTS.md already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
