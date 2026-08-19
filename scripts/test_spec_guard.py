#!/usr/bin/env python3
"""Keep the spec guard registration and decision contract honest.

Runs the command hook end to end -- payload on stdin, decision on stdout -- and
checks that Claude Code project settings actually register the tested script.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "spec_guard.py"
REPO = GUARD.parent.parent
SPECS = REPO / "specs"
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
    ("curl output",
     {"tool_name": "Bash",
      "tool_input": {"command": "curl -o specs/download.md https://example.invalid/file"}}),
    ("tar extraction",
     {"tool_name": "Bash",
      "tool_input": {"command": "tar -xf /tmp/archive.tar -C specs"}}),
    ("find deletion",
     {"tool_name": "Bash",
      "tool_input": {"command": "find specs -type f -delete"}}),
    ("chmod mutation",
     {"tool_name": "Bash",
      "tool_input": {"command": "chmod 600 specs/requirements.md"}}),
    ("git clone destination",
     {"tool_name": "Bash",
      "tool_input": {"command": "git clone https://example.invalid/repo specs/vendor"}}),
    ("PowerShell write",
     {"tool_name": "PowerShell",
      "tool_input": {"command": "Set-Content -Path specs/x.md -Value x"}}),
    ("PowerShell web output",
     {"tool_name": "PowerShell",
      "tool_input": {
          "command": "Invoke-WebRequest https://example.invalid -OutFile specs/download.md"
      }}),
    ("MCP filesystem write",
     {"tool_name": "mcp__filesystem__write_file",
      "tool_input": {"path": "specs/x.md", "content": "x"}}),
    ("MCP filesystem append",
     {"tool_name": "mcp__filesystem__append_file",
      "tool_input": {"path": "specs/requirements.md", "content": "x"}}),
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
    ("curl output elsewhere",
     {"tool_name": "Bash",
      "tool_input": {"command": "curl -o /tmp/download.md https://example.invalid/file"}}),
    ("tar extraction elsewhere",
     {"tool_name": "Bash",
      "tool_input": {"command": "tar -xf /tmp/archive.tar -C /tmp/unpack"}}),
    ("find deletion elsewhere",
     {"tool_name": "Bash",
      "tool_input": {"command": "find /tmp/unpack -type f -delete"}}),
    ("chmod elsewhere",
     {"tool_name": "Bash", "tool_input": {"command": "chmod 600 /tmp/result.md"}}),
    ("git clone elsewhere",
     {"tool_name": "Bash",
      "tool_input": {"command": "git clone https://example.invalid/repo /tmp/vendor"}}),
    ("a specs directory elsewhere",
     {"cwd": "/tmp/other-project", "tool_name": "Bash",
      "tool_input": {"command": "echo x > specs/result.md"}}),
    ("a tool that does not write",
     {"tool_name": "Read", "tool_input": {"file_path": "specs/requirements.md"}}),
    ("PowerShell read",
     {"tool_name": "PowerShell", "tool_input": {"command": "Get-Content specs/requirements.md"}}),
    ("PowerShell web output elsewhere",
     {"tool_name": "PowerShell",
      "tool_input": {
          "command": "Invoke-WebRequest https://example.invalid -OutFile /tmp/download.md"
      }}),
    ("MCP filesystem read",
     {"tool_name": "mcp__filesystem__read_file",
      "tool_input": {"path": "specs/requirements.md"}}),
    ("MCP write elsewhere",
     {"tool_name": "mcp__filesystem__write_file",
      "tool_input": {"path": "tests/result.txt", "content": "see specs/x.md"}}),
    ("MCP append elsewhere",
     {"tool_name": "mcp__filesystem__append_file",
      "tool_input": {"path": "tests/result.txt", "content": "x"}}),
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
    ("missing cwd",
     json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Write",
                 "tool_input": {"file_path": "specs/x.md", "content": "x"}})),
    ("relative cwd",
     json.dumps({"hook_event_name": "PreToolUse", "cwd": ".",
                 "tool_name": "Write",
                 "tool_input": {"file_path": "specs/x.md", "content": "x"}})),
]

CONFIG_BLOCK = [
    ("missing protected directory", []),
    ("relative protected directory", ["--protected-dir", "specs"]),
    ("filesystem root", ["--protected-dir", "/"]),
    ("non-directory target", ["--protected-dir", str(PROJECT_SETTINGS)]),
]


def invoke(raw: str,
           guard_args: list[str] | None = None,
           include_project_dir: bool = True) -> subprocess.CompletedProcess[str]:
    if guard_args is None:
        guard_args = ["--protected-dir", str(SPECS)]
    env = dict(os.environ)
    if include_project_dir:
        env["CLAUDE_PROJECT_DIR"] = str(REPO)
    else:
        env.pop("CLAUDE_PROJECT_DIR", None)
    return subprocess.run([sys.executable, str(GUARD), *guard_args], input=raw,
                          capture_output=True, text=True, timeout=20, env=env)


def run(payload: dict, protected_dir: Path = SPECS) -> dict | None:
    payload = {"hook_event_name": "PreToolUse", "cwd": str(REPO), **payload}
    proc = invoke(
        json.dumps(payload),
        ["--protected-dir", str(protected_dir)],
    )
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
    ask_rules = project.get("permissions", {}).get("ask", [])
    if not isinstance(ask_rules, list) or "Edit(/specs/**)" not in ask_rules:
        failures.append("project permissions do not ask on built-in spec edits")
    try:
        groups = project["hooks"]["PreToolUse"]
        group = groups[0]
        handler = group["hooks"][0]
    except (KeyError, IndexError, TypeError):
        failures.append("project settings do not register the spec guard hook")
        return
    if len(groups) != 1:
        failures.append("project settings must contain exactly one spec guard group")
    expected_tools = {
        "Bash", "Edit", "MultiEdit", "NotebookEdit", "PowerShell", "Write",
        "mcp__.*",
    }
    if set(group.get("matcher", "").split("|")) != expected_tools:
        failures.append("project hook does not cover the maintained tool set")
    if "if" in handler:
        failures.append("project hook must remain unfiltered")
    expected_args = [
        "${CLAUDE_PROJECT_DIR}/scripts/spec_guard.py",
        "--protected-dir",
        "${CLAUDE_PROJECT_DIR}/specs",
    ]
    if handler.get("type") != "command" or handler.get("command") != "python3":
        failures.append("project hook does not invoke the guard with python3")
    if handler.get("args") != expected_args:
        failures.append("project hook does not resolve the guard from the project root")


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

    valid_raw = json.dumps({
        "hook_event_name": "PreToolUse",
        "cwd": str(REPO),
        "tool_name": "Write",
        "tool_input": {"file_path": "specs/x.md", "content": "x"},
    })
    for label, guard_args in CONFIG_BLOCK:
        proc = invoke(valid_raw, guard_args)
        if proc.returncode != 2 or "blocking" not in proc.stderr:
            failures.append(
                f"{label}: expected blocking exit 2, got "
                f"{proc.returncode} / {proc.stderr!r}"
            )

    alternate = REPO / "tests"
    alternate_decision = run(
        {"tool_name": "Bash",
         "tool_input": {"command": "echo x > tests/result.txt"}},
        alternate,
    )
    alternate_got = (alternate_decision or {}).get(
        "hookSpecificOutput", {}
    ).get("permissionDecision")
    if alternate_got != "ask":
        failures.append(
            "configured alternate directory: "
            f"expected ask, got {alternate_got!r}"
        )
    unrelated_decision = run(
        {"tool_name": "Write",
         "tool_input": {"file_path": "specs/result.txt", "content": "x"}},
        alternate,
    )
    if unrelated_decision is not None:
        failures.append(
            "configured alternate directory: hard-coded specs path still matched"
        )

    root_spellings = (
        "${CLAUDE_PROJECT_DIR}",
        "$CLAUDE_PROJECT_DIR",
        "%CLAUDE_PROJECT_DIR%",
        "${env:CLAUDE_PROJECT_DIR}",
        "$env:CLAUDE_PROJECT_DIR",
    )
    for spelling in root_spellings:
        decision = run({
            "tool_name": "Bash",
            "tool_input": {"command": f'echo x > "{spelling}/specs/x.md"'},
        })
        got = (decision or {}).get(
            "hookSpecificOutput", {}
        ).get("permissionDecision")
        if got != "ask":
            failures.append(
                f"project root spelling {spelling!r}: expected ask, got {got!r}"
            )

    missing_root_raw = json.dumps({
        "hook_event_name": "PreToolUse",
        "cwd": str(REPO),
        "tool_name": "Bash",
        "tool_input": {
            "command": "echo x > $CLAUDE_PROJECT_DIR/specs/x.md",
        },
    })
    missing_root = invoke(missing_root_raw, include_project_dir=False)
    if missing_root.returncode != 2 or "blocking" not in missing_root.stderr:
        failures.append(
            "missing CLAUDE_PROJECT_DIR: expected blocking exit 2, got "
            f"{missing_root.returncode} / {missing_root.stderr!r}"
        )

    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        return 1
    print(
        f"spec guard: ok (registered, {len(ASK)} asked, "
        f"{len(ALLOW)} allowed, {len(BLOCK) + len(CONFIG_BLOCK)} blocked)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
