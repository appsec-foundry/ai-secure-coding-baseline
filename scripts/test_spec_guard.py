#!/usr/bin/env python3
"""Keep the spec guard honest: it asks on writes to specs/ and on nothing else.

Runs the hook end to end -- payload on stdin, decision on stdout -- so a change
to the contract fails here rather than silently in a session.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "spec_guard.py"
REPO = GUARD.parent.parent

ASK = [
    ("Write into the catalog",
     {"tool_name": "Write", "tool_input": {"file_path": str(REPO / "specs/requirements.md"),
                                           "content": "x"}}),
    ("Edit in a change directory",
     {"tool_name": "Edit", "tool_input": {"file_path": "specs/changes/foo/proposal.md",
                                          "new_string": "x"}}),
    ("redirect into a spec",
     {"tool_name": "Bash", "tool_input": {"command": "echo x > specs/requirements.md"}}),
    ("heredoc writing a spec",
     {"tool_name": "Bash", "tool_input": {"command": "cat <<EOF > specs/changes/a/tasks.md\nx\nEOF"}}),
    ("sed -i over the catalog",
     {"tool_name": "Bash", "tool_input": {"command": "sed -i 's/a/b/' specs/requirements.md"}}),
    ("removing a change directory",
     {"tool_name": "Bash", "tool_input": {"command": "rm -rf specs/changes/scope-the-note"}}),
    ("python one-liner naming a spec",
     {"tool_name": "Bash", "tool_input": {"command": "python3 -c \"open('specs/x.md','w')\""}}),
]

ALLOW = [
    ("the baseline itself",
     {"tool_name": "Write", "tool_input": {"file_path": str(REPO / "secure-coding-baseline.md"),
                                           "content": "x"}}),
    ("a test case",
     {"tool_name": "Write", "tool_input": {"file_path": "tests/cases/x/checks.json",
                                           "content": "{}"}}),
    ("specs elsewhere on disk",
     {"tool_name": "Write", "tool_input": {"file_path": "/tmp/other-project/specs/x.md",
                                           "content": "x"}}),
    ("reading a spec",
     {"tool_name": "Bash", "tool_input": {"command": "cat specs/requirements.md"}}),
    ("grepping the specs",
     {"tool_name": "Bash", "tool_input": {"command": "grep -n REPORT specs/requirements.md"}}),
    ("diffing the specs",
     {"tool_name": "Bash", "tool_input": {"command": "git diff -- specs/"}}),
    ("a write somewhere else",
     {"tool_name": "Bash", "tool_input": {"command": "echo x > tests/results/run.json"}}),
    ("a tool that does not write",
     {"tool_name": "Read", "tool_input": {"file_path": "specs/requirements.md"}}),
]


def run(payload: dict) -> dict | None:
    payload = {"hook_event_name": "PreToolUse", **payload}
    proc = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise AssertionError(f"guard exited {proc.returncode}: {proc.stderr[:300]}")
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def main() -> int:
    failures: list[str] = []

    for label, payload in ASK:
        decision = run(payload)
        got = (decision or {}).get("hookSpecificOutput", {}).get("permissionDecision")
        if got != "ask":
            failures.append(f"{label}: expected ask, got {got!r}")

    for label, payload in ALLOW:
        decision = run(payload)
        if decision is not None:
            failures.append(f"{label}: expected no decision, got {decision}")

    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        return 1
    print(f"spec guard: ok ({len(ASK)} asked, {len(ALLOW)} allowed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
