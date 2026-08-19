#!/usr/bin/env python3
"""Ask before an identifiable tool call writes under a protected directory.

`AGENTS.md` says nothing under `specs/` is written without the user's explicit
approval. That sentence binds a model that reads it. This Claude Code
`PreToolUse` hook reinforces it by turning a native file write, recognizable
shell write, or recognizable MCP file mutation into a permission prompt.

Scope
-----
The protected directory is required through `--protected-dir`; the hook
registration owns that policy. Native reads and recognized read-only shell
calls are untouched. Conservative writer checks can still ask when a protected
path is only a source; the guard favors an extra prompt over silently missing a
mutation.

Enforcement boundary
--------------------
The Bash and PowerShell arms ask when the command or hook working directory
identifies the protected directory and the command contains a recognized
writing construct.
The MCP arm asks only for recognizably mutating tool names with path-shaped
input fields. No pre-tool hook can infer that an otherwise opaque program or
script writes there when neither its name nor arguments reveal that effect. The
instruction and diff review remain authoritative for that case; prompting on
every shell command would obscure the approval the prompt is meant to record.
If the command hook cannot start or reaches its timeout, Claude Code renders no
hook decision; the native edit ask rule still covers built-in file tools, while
other tools fall back to their normal permission flow.

Contract
--------
Reads the Claude Code PreToolUse payload on stdin, prints an ask decision on
stdout when the call identifies a write under the configured directory, and
prints nothing for an allowed call. Missing configuration or malformed matched
input exits 2 so Claude Code blocks it.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path

# Tool -> field naming the file it writes.
WRITE_TOOLS = {
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}

# Shell constructs that change a file rather than read it. They are paired with
# a resolved protected target below; recognizing a writer alone does not prompt.
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
    "This call would change {target} under the protected directory "
    "{protected_dir}. AGENTS.md requires the user's explicit approval. Describe "
    "the entry -- the requirement, its source, the file it lands in -- and let "
    "the user decide. Reading protected files needs no approval."
)


class InvalidPayload(ValueError):
    """A matched hook call cannot be interpreted safely."""


class InvalidConfiguration(ValueError):
    """The hook did not identify a safe protected directory."""


def parse_protected_dir(argv: Sequence[str]) -> Path:
    """Return the required absolute protected directory from hook arguments."""
    if len(argv) != 2 or argv[0] != "--protected-dir" or not argv[1]:
        raise InvalidConfiguration("expected --protected-dir with one path")
    candidate = Path(argv[1]).expanduser()
    if not candidate.is_absolute():
        raise InvalidConfiguration("protected directory must be absolute")
    protected_dir = candidate.resolve()
    if protected_dir == Path(protected_dir.anchor):
        raise InvalidConfiguration("protected directory must not be a filesystem root")
    if protected_dir.exists() and not protected_dir.is_dir():
        raise InvalidConfiguration("protected directory points to a non-directory")
    return protected_dir


def expand_known_roots(value: str, cwd: Path) -> str:
    """Expand only Claude/PWD path spellings needed for target resolution."""
    replacements = {
        "${PWD}": str(cwd),
        "$PWD": str(cwd),
    }
    # Longest/containing spellings come first so a shorter token cannot partially
    # rewrite them before their exact replacement is considered.
    project_tokens = (
        "${env:CLAUDE_PROJECT_DIR}",
        "${CLAUDE_PROJECT_DIR}",
        "%CLAUDE_PROJECT_DIR%",
        "$env:CLAUDE_PROJECT_DIR",
        "$CLAUDE_PROJECT_DIR",
    )
    if any(token in value for token in project_tokens):
        configured_root = os.environ.get("CLAUDE_PROJECT_DIR")
        if not configured_root:
            raise InvalidPayload("CLAUDE_PROJECT_DIR is required to resolve the target")
        project_dir = Path(configured_root).expanduser()
        if not project_dir.is_absolute():
            raise InvalidPayload("CLAUDE_PROJECT_DIR must be absolute")
        replacements.update({token: str(project_dir.resolve())
                             for token in project_tokens})
    for token, replacement in replacements.items():
        value = value.replace(token, replacement)
    return value


def under_protected(path: str, protected_dir: Path, base: Path) -> bool:
    """True when the path names the configured directory or something below it."""
    if not path:
        return False
    candidate = Path(expand_known_roots(path, base)).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    resolved = candidate.resolve()
    return resolved == protected_dir or protected_dir in resolved.parents


def payload_cwd(payload: Mapping[str, object]) -> Path:
    """Return the absolute working directory reported by Claude Code."""
    value = payload.get("cwd")
    if not isinstance(value, str) or not value:
        raise InvalidPayload("cwd must be a non-empty string")
    cwd = Path(value).expanduser()
    if not cwd.is_absolute():
        raise InvalidPayload("cwd must be absolute")
    return cwd.resolve()


def protected_path_reference(protected_dir: Path) -> re.Pattern[str]:
    """Match embedded paths that contain the protected directory's basename."""
    name = re.escape(protected_dir.name)
    return re.compile(
        r"(?<![\w.-])(?:[A-Za-z]:)?(?:[~.\w-]*[\\/])*"
        + name
        + r"(?:[\\/][\w.~ -]*)?"
    )


def path_candidates(command: str, cwd: Path,
                    protected_dir: Path) -> Iterator[str]:
    """Yield shell tokens and embedded references to the protected directory."""
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
    pattern = protected_path_reference(protected_dir)
    yield from (match.group(0) for match in pattern.finditer(expanded))


def shell_targets(command: str, cwd: Path, tool_name: str,
                  protected_dir: Path) -> list[str]:
    """Protected paths that a writing shell command names, if any."""
    writes = SHELL_WRITES.search(command)
    if tool_name == "PowerShell":
        writes = writes or POWERSHELL_WRITES.search(command)
    if not writes:
        return []
    targets = {
        candidate
        for candidate in path_candidates(command, cwd, protected_dir)
        if under_protected(candidate, protected_dir, cwd)
    }
    if under_protected(str(cwd), protected_dir, cwd):
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


def mcp_targets(tool_name: str, tool_input: Mapping[str, object], cwd: Path,
                protected_dir: Path) -> list[str]:
    """Protected targets from a recognizably mutating MCP tool."""
    action = tool_name.rsplit("__", 1)[-1]
    if not MCP_MUTATION.search(action):
        return []
    return sorted({path for path in mcp_path_values(tool_input)
                   if under_protected(path, protected_dir, cwd)})


def decide(payload: dict, protected_dir: Path) -> dict | None:
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
        if not under_protected(path, protected_dir, cwd):
            return None
        target = path
    elif tool_name in {"Bash", "PowerShell"}:
        command = tool_input.get("command")
        if not isinstance(command, str) or not command:
            raise InvalidPayload(f"{tool_name} requires a command")
        targets = shell_targets(command, cwd, tool_name, protected_dir)
        if not targets:
            return None
        target = ", ".join(targets)
    elif tool_name.startswith("mcp__"):
        targets = mcp_targets(tool_name, tool_input, cwd, protected_dir)
        if not targets:
            return None
        target = ", ".join(targets)
    else:
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": REASON.format(
                target=target,
                protected_dir=protected_dir,
            ),
        }
    }


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    raw = sys.stdin.read()
    try:
        protected_dir = parse_protected_dir(argv)
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise InvalidPayload("hook payload must be an object")
        response = decide(payload, protected_dir)
    except (json.JSONDecodeError, InvalidConfiguration, InvalidPayload) as exc:
        print(f"spec guard: invalid input ({exc}); blocking", file=sys.stderr)
        return 2
    except Exception as exc:  # fail closed if target resolution itself breaks
        print(f"spec guard: internal {type(exc).__name__}; blocking", file=sys.stderr)
        return 2
    if response:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
