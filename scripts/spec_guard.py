#!/usr/bin/env python3
"""Put every write under `specs/` to the user before it happens.

`AGENTS.md` says nothing under `specs/` is written without the user's explicit
approval. That sentence binds a model that reads it. This hook binds the write:
it turns a Write, Edit, or shell command that would change a file under `specs/`
into a permission prompt, so the approval is an answer the user gave rather than
a rule the assistant remembered.

Scope
-----
Only this repository's `specs/` directory, resolved from this file's location.
Reading a spec is untouched -- the guard exists to keep changes from happening
silently, not to make the catalog harder to consult.

Shell commands
--------------
A shell command can reach a file in ways no matcher enumerates, so the Bash arm
asks whenever a command names a path under `specs/` together with a construct
that writes: a redirect, `tee`, `sed -i`, `rm`, `mv`, `cp`, a heredoc. Commands
that only read -- `cat`, `grep`, `git diff` -- pass. A write it fails to
recognise still lands in front of `make check` and the diff; a prompt on every
read would train the user to click through, which costs more than the gap.

Contract
--------
Reads the Claude Code PreToolUse payload on stdin, prints an ask decision on
stdout when the call would touch `specs/`, prints nothing otherwise, and always
exits 0. An unreadable payload is reported on stderr and allowed.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPECS = REPO / "specs"

# Tool -> field naming the file it writes.
WRITE_TOOLS = {
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}

# Shell constructs that change a file rather than read it.
SHELL_WRITES = re.compile(
    r"""
      (?<! [0-9<>] ) >>? (?! &)      # redirect, but not 2>&1 or a here-string
    | << -? \s* ["']? [A-Za-z_]      # heredoc
    | \b tee \b
    | \b sed \b [^\n|]* -i
    | \b (?: rm | mv | cp | install | truncate | touch | mkdir | ln ) \b
    | \b git \s+ (?: checkout | restore | apply | rm | mv | clean ) \b
    | \b (?: python3? | perl | ruby | node ) \b [^\n]* \s (?: -c | -e ) \s
    """,
    re.VERBOSE,
)

REASON = (
    "This call would change {target} under specs/. AGENTS.md: nothing under "
    "specs/ is written without the user's explicit approval. Describe the entry "
    "-- the requirement, its source, the file it lands in -- and let the user "
    "decide. Reading the specs needs no approval."
)


def under_specs(path: str) -> bool:
    """True when the path names something inside this repository's specs/."""
    if not path:
        return False
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return False
    return resolved == SPECS or SPECS in resolved.parents


def shell_targets(command: str) -> list[str]:
    """Paths under specs/ that a writing shell command names, if any."""
    if not SHELL_WRITES.search(command):
        return []
    try:
        words = shlex.split(command, comments=False)
    except ValueError:  # unbalanced quotes: fall back to whitespace
        words = command.split()
    # A heredoc body is one word to shlex only when quoted, so scan the raw text
    # too -- `python3 - <<EOF` carries its path inside the body.
    words += re.findall(r"[\w./~-]*specs/[\w./-]*", command)
    return sorted({w for w in words if under_specs(w.strip("'\"`,;()"))})


def decide(payload: dict) -> dict | None:
    """The ask decision for this call, or None to stay out of the way."""
    if payload.get("hook_event_name") not in (None, "PreToolUse"):
        return None
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return None

    if tool_name in WRITE_TOOLS:
        path = tool_input.get(WRITE_TOOLS[tool_name])
        if not isinstance(path, str) or not under_specs(path):
            return None
        target = path
    elif tool_name == "Bash":
        command = tool_input.get("command")
        if not isinstance(command, str):
            return None
        targets = shell_targets(command)
        if not targets:
            return None
        target = ", ".join(targets)
    else:
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": REASON.format(target=target),
        }
    }


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        print(f"spec guard: unreadable hook payload ({exc}); allowing", file=sys.stderr)
        return 0
    if not isinstance(payload, dict):
        print("spec guard: hook payload is not an object; allowing", file=sys.stderr)
        return 0
    response = decide(payload)
    if response:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
