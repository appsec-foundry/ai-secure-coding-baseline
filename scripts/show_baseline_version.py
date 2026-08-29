#!/usr/bin/env python3
"""Print the installed baseline ID for agent session-start hooks."""

import argparse
import json
import re
import sys
from pathlib import Path

BASELINE = "secure-coding-baseline.md"
MAX_BASELINE_BYTES = 256 * 1024
SEMVER_TEXT = (
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
BASELINE_ID_RE = re.compile(
    rf"^`baseline-id:\s*(?P<id>[a-z][a-z0-9-]*-{SEMVER_TEXT})`",
    re.MULTILINE,
)


def baseline_path() -> Path:
    """Find the baseline beside the managed helper or one directory above it."""
    helper_dir = Path(__file__).resolve().parent
    for candidate in (helper_dir / BASELINE, helper_dir.parent / BASELINE):
        if candidate.is_file() and not candidate.is_symlink():
            return candidate
    raise ValueError("installed baseline not found")


def baseline_id(path: Path) -> str:
    with path.open("rb") as handle:
        content = handle.read(MAX_BASELINE_BYTES + 1)
    if not content or len(content) > MAX_BASELINE_BYTES:
        raise ValueError("installed baseline has an invalid size")
    text = content.decode("utf-8")
    matches = list(BASELINE_ID_RE.finditer(text))
    if len(matches) != 1:
        raise ValueError("installed baseline has no unique baseline ID")
    return matches[0].group("id")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        choices=("message", "json"),
        default="message",
        help="plain startup banner or hook JSON with a visible system message",
    )
    args = parser.parse_args(argv)
    try:
        message = f"AI Secure Coding Baseline active: {baseline_id(baseline_path())}"
    except (OSError, UnicodeDecodeError, ValueError):
        print("Could not read the installed AI Secure Coding Baseline ID.", file=sys.stderr)
        return 1

    if args.output == "json":
        print(json.dumps({"systemMessage": message}))
    else:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
