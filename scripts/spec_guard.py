#!/usr/bin/env python3
"""Ask before an identifiable tool call writes under this repository's specs/.

`AGENTS.md` says nothing under `specs/` is written without the user's explicit
approval. That sentence binds a model that reads it. This Claude Code
`PreToolUse` hook reinforces it by turning a native file write, recognizable
shell write, or recognizable MCP file mutation into a permission prompt.

Scope
-----
Only this repository's `specs/` directory, resolved from this file's location.
Native reads and recognized read-only shell calls are untouched. Conservative
writer checks can still ask when a spec path is only a source; the guard favors
an extra prompt over silently missing a mutation.

Enforcement boundary
--------------------
The Bash and PowerShell arms ask when the command or hook working directory
identifies `specs/` and the command contains a recognized writing construct.
The MCP arm asks only for recognizably mutating tool names with path-shaped
input fields. No pre-tool hook can infer that an otherwise opaque program or
script writes `specs/` when neither its name nor arguments reveal that effect.
The instruction and diff review remain authoritative for that case; prompting
on every shell command would obscure the approval the prompt is meant to record.
If the command hook cannot start or reaches its timeout, Claude Code renders no
hook decision; the native edit ask rule still covers built-in file tools, while
other tools fall back to their normal permission flow.

Contract
--------
Reads the Claude Code PreToolUse payload on stdin, prints an ask decision on
stdout when the call identifies a write under `specs/`, and prints nothing for
an allowed call. Malformed matched input exits 2 so Claude Code blocks it.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from collections.abc import Iterator, Mapping, Sequence
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

# Shell constructs that change a file rather than read it. They are paired with
# a resolved specs/ target below; recognizing a writer alone does not prompt.
SHELL_WRITES = re.compile(
    r"""
      (?<! [<>] ) (?: [0-9]+ )? >>? (?! [>&] )  # output redirect, not 2>&1
    | << -? \s* ["']? [A-Za-z_]      # heredoc
    | \b tee \b
    | \b sponge \b
    | \b sed \b [^\n|]* -i
    | \b dd \b [^\n|;&]* \b of \s* =
    | \b (?: rm | mv | cp | install | truncate | touch | mkdir | ln | chmod ) \b
    | \b (?: rsync | unzip ) \b
    | \b git \s+ (?: checkout | restore | apply | rm | mv | clean | clone ) \b
    | \b curl \b [^\n|;&]* \s (?: -o | --output ) \b
    | \b tar \b [^\n|;&]* \s (?: -[A-Za-z]*x[A-Za-z]* | --extract ) \b
    | \b find \b [^\n|;&]* \s -delete \b
    | \b (?: python3? | perl | ruby | node ) \b [^\n]* \s (?: -c | -e ) \s
    """,
    re.VERBOSE,
)

POWERSHELL_WRITES = re.compile(
    r"""
      \b (?:
        Add-Content | Clear-Content | Copy-Item | Move-Item | New-Item |
        Out-File | Remove-Item | Rename-Item | Set-Content | Tee-Object
      ) \b
    | \b Invoke-WebRequest \b [^\n|;]* (?<! \w ) -OutFile \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

PATH_REFERENCE = re.compile(
    r"(?<![\w.-])(?:[A-Za-z]:)?(?:[~.\w-]*[\\/])*"
    r"specs(?:[\\/][\w.~ -]*)?"
)

MCP_MUTATION = re.compile(
    r"(?:^|_)(?:append|apply|copy|create|delete|edit|mkdir|move|patch|remove|rename|"
    r"save|touch|truncate|update|upload|write)(?:_|$)",
    re.IGNORECASE,
)

PATH_KEYS = {
    "dest",
    "destination",
    "directory",
    "dir",
    "file",
    "file_path",
    "filepath",
    "new_path",
    "notebook_path",
    "old_path",
    "path",
    "paths",
    "source_path",
    "target",
    "target_path",
}

REASON = (
    "This call would change {target} under specs/. AGENTS.md: nothing under "
    "specs/ is written without the user's explicit approval. Describe the entry "
    "-- the requirement, its source, the file it lands in -- and let the user "
    "decide. Reading the specs needs no approval."
)


class InvalidPayload(ValueError):
    """A matched hook call cannot be interpreted safely."""


def expand_known_roots(value: str, cwd: Path) -> str:
    """Expand only Claude/PWD path spellings needed for target resolution."""
    replacements = {
        "${CLAUDE_PROJECT_DIR}": str(REPO),
        "$CLAUDE_PROJECT_DIR": str(REPO),
        "%CLAUDE_PROJECT_DIR%": str(REPO),
        "${env:CLAUDE_PROJECT_DIR}": str(REPO),
        "$env:CLAUDE_PROJECT_DIR": str(REPO),
        "${PWD}": str(cwd),
        "$PWD": str(cwd),
    }
    for token, replacement in replacements.items():
        value = value.replace(token, replacement)
    return value


def under_specs(path: str, base: Path = REPO) -> bool:
    """True when the path names something inside this repository's specs/."""
    if not path:
        return False
    candidate = Path(expand_known_roots(path, base)).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    resolved = candidate.resolve()
    return resolved == SPECS or SPECS in resolved.parents


def payload_cwd(payload: Mapping[str, object]) -> Path:
    """Return the absolute hook cwd, defaulting to the repository for tests."""
    value = payload.get("cwd")
    if value is None:
        return REPO
    if not isinstance(value, str) or not value:
        raise InvalidPayload("cwd must be a non-empty string")
    cwd = Path(value).expanduser()
    if not cwd.is_absolute():
        cwd = REPO / cwd
    return cwd.resolve()


def path_candidates(command: str, cwd: Path) -> Iterator[str]:
    """Yield shell tokens and embedded path references that may name specs/."""
    expanded = expand_known_roots(command, cwd)
    try:
        words = shlex.split(expanded, comments=False)
    except ValueError:  # unbalanced quotes: retain conservative token scanning
        words = expanded.split()
    for word in words:
        cleaned = word.strip("'\"`,;()[]{}<>")
        if cleaned:
            yield cleaned
        if "=" in cleaned:
            value = cleaned.split("=", 1)[1]
            if value:
                yield value.strip("'\"")
    yield from (match.group(0) for match in PATH_REFERENCE.finditer(expanded))


def shell_targets(command: str, cwd: Path, tool_name: str) -> list[str]:
    """Paths under specs/ that a writing shell command names, if any."""
    writes = SHELL_WRITES.search(command)
    if tool_name == "PowerShell":
        writes = writes or POWERSHELL_WRITES.search(command)
    if not writes:
        return []
    targets = {candidate for candidate in path_candidates(command, cwd)
               if under_specs(candidate, cwd)}
    if under_specs(str(cwd)):
        targets.add(str(cwd))
    return sorted(targets)


def string_values(value: object) -> Iterator[str]:
    """Yield strings from a path-valued MCP field without inspecting content."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            yield from string_values(item)


def mcp_path_values(value: object) -> Iterator[str]:
    """Yield values from recursively nested MCP fields that are path-shaped."""
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in PATH_KEYS or normalized.endswith(("_path", "_paths")):
                yield from string_values(child)
            else:
                yield from mcp_path_values(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from mcp_path_values(child)


def mcp_targets(tool_name: str, tool_input: Mapping[str, object], cwd: Path) -> list[str]:
    """Resolved specs/ targets from a recognizably mutating MCP tool."""
    action = tool_name.rsplit("__", 1)[-1]
    if not MCP_MUTATION.search(action):
        return []
    return sorted({path for path in mcp_path_values(tool_input)
                   if under_specs(path, cwd)})


def decide(payload: dict) -> dict | None:
    """The ask decision for this call, or None to stay out of the way."""
    if payload.get("hook_event_name") != "PreToolUse":
        raise InvalidPayload("expected a PreToolUse payload")
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        raise InvalidPayload("tool_name and tool_input are required")
    cwd = payload_cwd(payload)

    if tool_name in WRITE_TOOLS:
        path = tool_input.get(WRITE_TOOLS[tool_name])
        if not isinstance(path, str) or not path:
            raise InvalidPayload(f"{tool_name} requires a path")
        if not under_specs(path, cwd):
            return None
        target = path
    elif tool_name in {"Bash", "PowerShell"}:
        command = tool_input.get("command")
        if not isinstance(command, str) or not command:
            raise InvalidPayload(f"{tool_name} requires a command")
        targets = shell_targets(command, cwd, tool_name)
        if not targets:
            return None
        target = ", ".join(targets)
    elif tool_name.startswith("mcp__"):
        targets = mcp_targets(tool_name, tool_input, cwd)
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
        if not isinstance(payload, dict):
            raise InvalidPayload("hook payload must be an object")
        response = decide(payload)
    except (json.JSONDecodeError, InvalidPayload) as exc:
        print(f"spec guard: invalid hook payload ({exc}); blocking", file=sys.stderr)
        return 2
    except Exception as exc:  # fail closed if target resolution itself breaks
        print(f"spec guard: internal {type(exc).__name__}; blocking", file=sys.stderr)
        return 2
    if response:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
