#!/usr/bin/env python3
"""Block a small set of unsafe edits through Claude Code's PreToolUse hook.

This example checks only the added text supplied by supported editing tools.
It is not a complete baseline enforcement mechanism.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from rules import RULES, Rule
except Exception:
    print("secure-coding gate: rule configuration unavailable; blocking",
          file=sys.stderr)
    raise SystemExit(2) from None


SELF_DIR = Path(os.path.realpath(Path(__file__).resolve().parent))

# Tool name -> (path field, added-text field).
TOOLS = {
    "Write": ("file_path", "content"),
    "Edit": ("file_path", "new_string"),
    "NotebookEdit": ("notebook_path", "new_source"),
}


@dataclass(frozen=True)
class Finding:
    rule: Rule
    line: int
    excerpt: str


class HookInputError(ValueError):
    """The matched hook call does not have the expected PreToolUse shape."""


def added_text(tool_name: str, tool_input: dict) -> tuple[str, str] | None:
    """Return the target path and added text for a supported editing tool."""
    entry = TOOLS.get(tool_name)
    if not entry:
        return None
    path_field, text_field = entry
    path = tool_input.get(path_field)
    text = tool_input.get(text_field)
    if not isinstance(path, str) or not path or not isinstance(text, str):
        return None
    return path, text


def scans(path: str) -> bool:
    """Exclude the example itself so its patterns and tests remain editable."""
    try:
        target = Path(os.path.realpath(path))
    except OSError:
        return True
    return SELF_DIR not in target.parents


def scan(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        match = rule.pattern.search(text)
        if not match:
            continue
        findings.append(
            Finding(
                rule=rule,
                line=text.count("\n", 0, match.start()) + 1,
                excerpt=match.group(0).strip()[:120],
            )
        )
    return findings


def reason(path: str, findings: list[Finding]) -> str:
    lines = [f"Blocked by the example secure-coding gate: {path}"]
    for finding in findings:
        lines.extend(
            (
                "",
                f"[{finding.rule.rule_id}] {finding.rule.title}",
                f"  line {finding.line}: {finding.excerpt}",
                f"  {finding.rule.guidance}",
            )
        )
    return "\n".join(lines)


def decide(payload: dict) -> dict | None:
    """Return a Claude Code deny response, or None when the edit is allowed."""
    if payload.get("hook_event_name") != "PreToolUse":
        raise HookInputError("unexpected hook event")
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        raise HookInputError("missing tool input")
    if tool_name not in TOOLS:
        return None
    target = added_text(tool_name, tool_input)
    if not target:
        raise HookInputError("invalid editing tool input")
    path, text = target
    if not scans(path):
        return None
    findings = scan(text)
    if not findings:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason(path, findings),
        }
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        print(f"secure-coding gate: unreadable hook payload ({exc}); blocking",
              file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("secure-coding gate: hook payload is not an object; blocking",
              file=sys.stderr)
        return 2
    try:
        response = decide(payload)
    except HookInputError as exc:
        print(f"secure-coding gate: {exc}; blocking", file=sys.stderr)
        return 2
    if response:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
