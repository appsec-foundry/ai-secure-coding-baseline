#!/usr/bin/env python3
"""Keep the spec guard registration and decision contract honest.

Runs the command hook end to end -- payload on stdin, decision on stdout -- and
checks that Claude Code project settings actually register the tested script.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "spec_guard.py"
REPO = GUARD.parent.parent
PROJECT_SETTINGS = REPO / ".claude/settings.json"

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
    ("relative write from a specs cwd",
     {"cwd": str(REPO / "specs"), "tool_name": "Bash",
      "tool_input": {"command": "touch changes/x.md"}}),
    ("project-root variable",
     {"tool_name": "Bash",
      "tool_input": {"command": "echo x > \"$CLAUDE_PROJECT_DIR/specs/x.md\""}}),
    ("dd output",
     {"tool_name": "Bash", "tool_input": {"command": "printf x | dd of=specs/x.md"}}),
    ("stderr redirect",
     {"tool_name": "Bash", "tool_input": {"command": "command 2> specs/error.log"}}),
    ("PowerShell write",
     {"tool_name": "PowerShell",
      "tool_input": {"command": "Set-Content -Path specs/x.md -Value x"}}),
    ("MCP filesystem write",
     {"tool_name": "mcp__filesystem__write_file",
      "tool_input": {"path": "specs/x.md", "content": "x"}}),
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
    ("a specs directory elsewhere",
     {"cwd": "/tmp/other-project", "tool_name": "Bash",
      "tool_input": {"command": "echo x > specs/result.md"}}),
    ("a tool that does not write",
     {"tool_name": "Read", "tool_input": {"file_path": "specs/requirements.md"}}),
    ("PowerShell read",
     {"tool_name": "PowerShell", "tool_input": {"command": "Get-Content specs/requirements.md"}}),
    ("MCP filesystem read",
     {"tool_name": "mcp__filesystem__read_file",
      "tool_input": {"path": "specs/requirements.md"}}),
    ("MCP write elsewhere",
     {"tool_name": "mcp__filesystem__write_file",
      "tool_input": {"path": "tests/result.txt", "content": "see specs/x.md"}}),
]

BLOCK = [
    ("malformed JSON", "{"),
    ("non-object payload", "[]"),
    ("missing Bash command",
     json.dumps({"hook_event_name": "PreToolUse", "cwd": str(REPO),
                 "tool_name": "Bash", "tool_input": {}})),
    ("missing Write path",
     json.dumps({"hook_event_name": "PreToolUse", "cwd": str(REPO),
                 "tool_name": "Write", "tool_input": {"content": "x"}})),
]


def invoke(raw: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(GUARD)], input=raw,
                          capture_output=True, text=True, timeout=20)


def run(payload: dict) -> dict | None:
    payload = {"hook_event_name": "PreToolUse", "cwd": str(REPO), **payload}
    proc = invoke(json.dumps(payload))
    if proc.returncode != 0:
        raise AssertionError(f"guard exited {proc.returncode}: {proc.stderr[:300]}")
    out = proc.stdout.strip()
    return json.loads(out) if out else None


def check_registration(failures: list[str]) -> None:
    """The tested hook must be the hook Claude Code loads for this project."""
    try:
        project = json.loads(PROJECT_SETTINGS.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"project hook registration is unreadable: {exc}")
        return
    try:
        groups = project["hooks"]["PreToolUse"]
        write_group = next(group for group in groups if group.get("matcher") == "Write")
        fallback_group = next(
            group for group in groups if group.get("matcher") != "Write"
        )
        write_handler = write_group["hooks"][0]
        fallback_handler = fallback_group["hooks"][0]
    except (KeyError, IndexError, StopIteration, TypeError):
        failures.append("project settings do not register the split PreToolUse hooks")
        return
    if len(groups) != 2:
        failures.append("project settings must contain exactly two spec guard groups")
    if write_handler.get("if") != "Write(/specs/**)":
        failures.append("project Write hook is not filtered from the project root")
    fallback_tools = {
        "Bash", "Edit", "MultiEdit", "NotebookEdit", "PowerShell", "mcp__.*",
    }
    if set(fallback_group.get("matcher", "").split("|")) != fallback_tools:
        failures.append("project fallback hook does not cover the maintained tool set")
    if "if" in fallback_handler:
        failures.append("project fallback hook must remain unfiltered")
    expected_args = ["${CLAUDE_PROJECT_DIR}/scripts/spec_guard.py"]
    for label, handler in (("Write", write_handler), ("fallback", fallback_handler)):
        if handler.get("type") != "command" or handler.get("command") != "python3":
            failures.append(f"project {label} hook does not invoke the guard with python3")
        if handler.get("args") != expected_args:
            failures.append(
                f"project {label} hook does not resolve the guard from the project root"
            )


def main() -> int:
    failures: list[str] = []

    check_registration(failures)

    for label, payload in ASK:
        decision = run(payload)
        got = (decision or {}).get("hookSpecificOutput", {}).get("permissionDecision")
        if got != "ask":
            failures.append(f"{label}: expected ask, got {got!r}")

    for label, payload in ALLOW:
        decision = run(payload)
        if decision is not None:
            failures.append(f"{label}: expected no decision, got {decision}")

    for label, raw in BLOCK:
        proc = invoke(raw)
        if proc.returncode != 2 or "blocking" not in proc.stderr:
            failures.append(
                f"{label}: expected blocking exit 2, got {proc.returncode} / {proc.stderr!r}"
            )

    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        return 1
    print(
        f"spec guard: ok (registered, {len(ASK)} asked, "
        f"{len(ALLOW)} allowed, {len(BLOCK)} blocked)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
