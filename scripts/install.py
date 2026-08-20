#!/usr/bin/env python3
"""Install, discover, and update the baseline without overwriting user work."""

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parent.parent
BASELINE = "secure-coding-baseline.md"
SOURCE = REPO / BASELINE
TOOLS = ("claude", "codex", "copilot")
TOOL_LABELS = {
    "claude": "Claude Code",
    "codex": "Codex",
    "copilot": "GitHub Copilot",
}

OFFICIAL_NAME = "aisec"
GITHUB_REPOSITORY = "matthiasrohr/ai-secure-coding-baseline"
LATEST_RELEASE_URL = (
    f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
)
CONTENTS_URL = (
    f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{BASELINE}"
)
API_VERSION = "2026-03-10"
ONLINE_TIMEOUT = 4
MAX_BASELINE_BYTES = 256 * 1024
MAX_INSTRUCTION_BYTES = 512 * 1024
MAX_API_BYTES = 512 * 1024
MAX_REGISTRY_BYTES = 128 * 1024
MAX_PROJECTS = 200
REGISTRY_SCHEMA = 1

SEMVER_TEXT = (
    r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
BASELINE_ID_RE = re.compile(
    rf"^`baseline-id:\s*(?P<name>[a-z][a-z0-9-]*)-"
    rf"(?P<version>{SEMVER_TEXT})`",
    re.MULTILINE,
)
RELEASE_TAG_RE = re.compile(
    rf"^(?:v|{OFFICIAL_NAME}-)?(?P<version>{SEMVER_TEXT})$"
)


@total_ordering
@dataclass(frozen=True, eq=False)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    metadata: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value: str) -> "SemVer":
        match = re.fullmatch(
            r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\."
            r"(?P<patch>0|[1-9]\d*)"
            r"(?:-(?P<pre>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
            r"(?:\+(?P<meta>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?",
            value,
        )
        if not match:
            raise ValueError("invalid semantic version")
        prerelease = tuple((match.group("pre") or "").split("."))
        metadata = tuple((match.group("meta") or "").split("."))
        if any(item.isdigit() and len(item) > 1 and item.startswith("0") for item in prerelease):
            raise ValueError("numeric prerelease identifiers cannot have leading zeroes")
        return cls(
            int(match.group("major")),
            int(match.group("minor")),
            int(match.group("patch")),
            tuple(item for item in prerelease if item),
            tuple(item for item in metadata if item),
        )

    def _core(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.patch

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self._core() == other._core() and self.prerelease == other.prerelease

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        if self._core() != other._core():
            return self._core() < other._core()
        if not self.prerelease:
            return False
        if not other.prerelease:
            return True
        for left, right in zip(self.prerelease, other.prerelease):
            if left == right:
                continue
            left_numeric, right_numeric = left.isdigit(), right.isdigit()
            if left_numeric and right_numeric:
                return int(left) < int(right)
            if left_numeric != right_numeric:
                return left_numeric
            return left < right
        return len(self.prerelease) < len(other.prerelease)

    def __str__(self) -> str:
        value = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            value += "-" + ".".join(self.prerelease)
        if self.metadata:
            value += "+" + ".".join(self.metadata)
        return value


@dataclass(frozen=True)
class Baseline:
    name: str
    version: SemVer
    content: bytes
    origin: str

    @property
    def baseline_id(self) -> str:
        return f"{self.name}-{self.version}"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    @property
    def is_official(self) -> bool:
        return self.name == OFFICIAL_NAME and not self.version.metadata


@dataclass(frozen=True)
class Installation:
    kind: str
    root: Path
    source: Path
    baseline: Baseline
    tools: tuple[str, ...]
    tracked_digest: str | None = None

    @property
    def label(self) -> str:
        if self.kind == "project":
            return f"project {display_path(self.root)}"
        if self.kind == "user":
            return "user-wide"
        if self.kind == "legacy-user":
            return f"user-wide (linked to checkout {display_path(self.source.parent)})"
        return f"unmanaged file {display_path(self.source)}"

    def has_update(self, available: Baseline) -> bool:
        return (
            self.kind != "unmanaged"
            and self.baseline.is_official
            and (
                self.baseline.version < available.version
                or (
                    self.baseline.version == available.version
                    and self.baseline.digest != available.digest
                )
            )
        )


def display_path(path: Path) -> str:
    """Quote paths so control characters cannot alter terminal output."""
    return repr(str(path))


def parse_baseline(content: bytes, origin: str) -> Baseline:
    if not content or len(content) > MAX_INSTRUCTION_BYTES:
        raise ValueError("baseline content has an invalid size")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("baseline content is not UTF-8") from error
    matches = list(BASELINE_ID_RE.finditer(text))
    if len(matches) != 1:
        raise ValueError("expected exactly one baseline-id")
    match = matches[0]
    return Baseline(
        match.group("name"),
        SemVer.parse(match.group("version")),
        content,
        origin,
    )


def read_limited(path: Path, limit: int) -> bytes:
    with path.open("rb") as handle:
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise ValueError("file is too large")
    return content


def read_baseline(path: Path) -> Baseline:
    return parse_baseline(read_limited(path, MAX_INSTRUCTION_BYTES), str(path))


def bundled_baseline() -> Baseline:
    return parse_baseline(read_limited(SOURCE, MAX_BASELINE_BYTES), "bundled checkout")


class _GitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        destination = urllib.parse.urlsplit(new_url)
        if destination.scheme != "https" or destination.netloc != "api.github.com":
            raise urllib.error.HTTPError(
                new_url, code, "refused cross-host update redirect", headers, file_pointer
            )
        return super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )


def _read_json_url(url: str) -> object:
    destination = urllib.parse.urlsplit(url)
    if destination.scheme != "https" or destination.netloc != "api.github.com":
        raise ValueError("unexpected update server")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-secure-coding-baseline-setup",
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    opener = urllib.request.build_opener(_GitHubRedirectHandler())
    with opener.open(request, timeout=ONLINE_TIMEOUT) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.netloc != "api.github.com":
            raise ValueError("unexpected update server")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_API_BYTES:
            raise ValueError("update response is too large")
        payload = response.read(MAX_API_BYTES + 1)
    if len(payload) > MAX_API_BYTES:
        raise ValueError("update response is too large")
    return json.loads(payload.decode("utf-8"))


def fetch_release_baseline(
    fetch_json: Callable[[str], object] = _read_json_url,
) -> Baseline:
    release = fetch_json(LATEST_RELEASE_URL)
    if not isinstance(release, dict):
        raise ValueError("invalid release response")
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("latest release is not stable")
    tag = release.get("tag_name")
    if not isinstance(tag, str) or len(tag) > 100:
        raise ValueError("release has no valid tag")
    tag_match = RELEASE_TAG_RE.fullmatch(tag)
    if not tag_match:
        raise ValueError("release tag does not contain a supported version")
    tag_version = SemVer.parse(tag_match.group("version"))

    query = urllib.parse.urlencode({"ref": tag})
    payload = fetch_json(f"{CONTENTS_URL}?{query}")
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise ValueError("release baseline is not a file")
    if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
        raise ValueError("release baseline has an unsupported encoding")
    try:
        encoded = "".join(payload["content"].splitlines())
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("release baseline is not valid base64") from error
    if len(content) > MAX_BASELINE_BYTES:
        raise ValueError("release baseline is too large")
    baseline = parse_baseline(content, f"GitHub release {tag}")
    if not baseline.content.startswith(b"# AI Secure Coding Baseline\n"):
        raise ValueError("release baseline has an unexpected format")
    if not baseline.is_official or baseline.version != tag_version:
        raise ValueError("release tag and baseline-id do not match")
    return baseline


def latest_available(check_online: bool) -> tuple[Baseline, str]:
    bundled = bundled_baseline()
    if not check_online:
        return bundled, "Online check skipped; using the bundled baseline."
    try:
        released = fetch_release_baseline()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return bundled, "No published release found; using the bundled baseline."
        return bundled, "Online check unavailable; using the bundled baseline."
    except (OSError, ValueError, json.JSONDecodeError):
        return bundled, "Online check unavailable; using the bundled baseline."
    if bundled.version > released.version:
        return bundled, (
            f"Bundled {bundled.version} is newer than published {released.version}; "
            "using the bundled baseline."
        )
    if released.version > bundled.version:
        return released, f"Published baseline {released.version} is available."
    return released, f"Published baseline {released.version} is current."


def project_targets(root: Path) -> dict[str, list[tuple[str, Path]]]:
    return {
        "claude": [("link", root / ".claude" / "rules" / BASELINE)],
        "codex": [("link", root / "AGENTS.md")],
        "copilot": [("link", root / ".github" / "copilot-instructions.md")],
    }


def user_data_root(home: Path) -> Path:
    return home / ".local" / "share" / "ai-secure-coding-baseline"


def user_source(home: Path) -> Path:
    return user_data_root(home) / BASELINE


def user_targets(home: Path) -> dict[str, list[tuple[str, Path]]]:
    return {
        "claude": [
            ("link", home / ".claude" / BASELINE),
            ("import_line", home / ".claude" / "CLAUDE.md"),
        ],
        "codex": [("link", home / ".codex" / "AGENTS.md")],
        "copilot": [],
    }


def link_text(target: Path, source: Path, *, relative: bool) -> str:
    """Inside a project the link stays relative, so a clone keeps working."""
    return os.path.relpath(source, target.parent) if relative else str(source)


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with path.open("xb") as handle:
            created = True
            handle.write(content)
    except BaseException:
        if created and path.exists() and not path.is_symlink():
            path.unlink()
        raise


def _atomic_replace(path: Path, content: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def place_baseline(
    root: Path,
    report: list[str],
    content: bytes | None = None,
    *,
    create_root: bool = False,
) -> Path | None:
    """Place one real baseline file, refusing foreign or invalid occupants."""
    local = root / BASELINE
    if local.resolve() == SOURCE.resolve():
        return local
    if local.is_symlink():
        report.append(f"blocked {local}: is a symlink, inspect it first")
        return None
    if local.exists():
        if not local.is_file():
            report.append(f"blocked {local}: is not a regular file")
            return None
        try:
            read_baseline(local)
        except (OSError, ValueError):
            report.append(f"blocked {local}: exists but is not a valid baseline")
            return None
        return local
    payload = content if content is not None else bundled_baseline().content
    if not root.is_dir():
        if not create_root:
            report.append(f"blocked {root}: project directory does not exist")
            return None
        root.mkdir(parents=True, exist_ok=True)
    _write_new(local, payload)
    report.append(f"added {local}")
    return local


def install_link(
    target: Path,
    source: Path,
    report: list[str],
    *,
    relative: bool,
) -> None:
    link = link_text(target, source, relative=relative)
    if target.is_symlink():
        if Path(os.readlink(target)) == Path(link):
            report.append(f"in place {target}")
            return
        report.append(f"blocked {target}: points elsewhere, remove it first")
        return
    if target.exists():
        report.append(
            f"blocked {target}: exists — append {source.name} to it by hand"
        )
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(link)
    report.append(f"linked {target} -> {link}")


def _instruction_lines(target: Path) -> list[str]:
    content = read_limited(target, MAX_INSTRUCTION_BYTES)
    return content.decode("utf-8").splitlines()


def install_import_line(target: Path, source: Path, report: list[str]) -> None:
    line = f"@{source}"
    if target.exists():
        try:
            lines = _instruction_lines(target)
        except (OSError, UnicodeDecodeError, ValueError):
            report.append(f"blocked {target}: cannot safely read existing file")
            return
        if line in lines:
            report.append(f"in place {target}")
        else:
            report.append(f"blocked {target}: exists — add the line {line!r} by hand")
        return
    if target.is_symlink():
        report.append(f"blocked {target}: is a broken symlink")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    _write_new(target, f"{line}\n".encode())
    report.append(f"wrote {target}")


def install(
    tools: list[str],
    root: Path,
    home: Path | None,
    *,
    content: bytes | None = None,
) -> list[str]:
    report: list[str] = []
    if home is not None:
        targets = user_targets(home)
        source = place_baseline(
            user_data_root(home), report, content, create_root=True
        )
        relative = False
    else:
        targets = project_targets(root)
        source = place_baseline(root, report, content)
        relative = True
    if source is None:
        return report

    for tool in tools:
        actions = targets[tool]
        if not actions:
            report.append(f"skipped {tool}: no documented location for this scope")
            continue
        for kind, target in actions:
            if kind == "link":
                install_link(target, source, report, relative=relative)
            else:
                install_import_line(target, source, report)
    return report


def registry_path(home: Path) -> Path:
    return home / ".config" / "ai-secure-coding-baseline" / "installations.json"


def empty_registry() -> dict[str, object]:
    return {"schema": REGISTRY_SCHEMA, "projects": {}, "user": None}


def load_registry(path: Path) -> tuple[dict[str, object], bool, str | None]:
    if not path.exists() and not path.is_symlink():
        return empty_registry(), True, None
    if path.is_symlink() or not path.is_file():
        return empty_registry(), False, "Installation registry is not a regular file."
    try:
        raw = read_limited(path, MAX_REGISTRY_BYTES)
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return empty_registry(), False, "Installation registry is invalid; it was not changed."
    if not isinstance(data, dict) or data.get("schema") != REGISTRY_SCHEMA:
        return empty_registry(), False, "Installation registry has an unsupported format."
    projects = data.get("projects")
    user = data.get("user")
    if not isinstance(projects, dict) or len(projects) > MAX_PROJECTS:
        return empty_registry(), False, "Installation registry has invalid project entries."
    if user is not None and not isinstance(user, dict):
        return empty_registry(), False, "Installation registry has an invalid user entry."
    return data, True, None


def save_registry(path: Path, registry: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(registry, indent=2, sort_keys=True) + "\n").encode()
    if len(payload) > MAX_REGISTRY_BYTES:
        raise ValueError("installation registry is too large")
    if path.is_symlink():
        raise ValueError("installation registry is a symlink")
    if path.exists():
        _atomic_replace(path, payload)
        os.chmod(path, 0o600)
    else:
        _write_new(path, payload)
        os.chmod(path, 0o600)


def _entry_digest(entry: object) -> str | None:
    if not isinstance(entry, dict):
        return None
    digest = entry.get("sha256")
    if isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest):
        return digest
    return None


def _link_points_to(target: Path, source: Path) -> bool:
    return target.is_symlink() and target.resolve(strict=False) == source.resolve(
        strict=False
    )


def _import_contains(target: Path, source: Path) -> bool:
    if not target.is_file():
        return False
    try:
        return f"@{source}" in _instruction_lines(target)
    except (OSError, UnicodeDecodeError, ValueError):
        return False


def installed_tools(
    targets: dict[str, list[tuple[str, Path]]], source: Path
) -> tuple[str, ...]:
    found: list[str] = []
    for tool, actions in targets.items():
        if not actions:
            continue
        matches = []
        for kind, target in actions:
            if kind == "link":
                matches.append(_link_points_to(target, source))
            else:
                matches.append(_import_contains(target, source))
        if all(matches):
            found.append(tool)
    return tuple(found)


def scan_project(root: Path, entry: object = None) -> Installation | None:
    source = root / BASELINE
    if source.is_symlink() or not source.is_file():
        return None
    try:
        baseline = read_baseline(source)
    except (OSError, ValueError):
        return None
    tools = installed_tools(project_targets(root), source)
    if not tools and not isinstance(entry, dict):
        return None
    return Installation(
        "project", root, source, baseline, tools, _entry_digest(entry)
    )


def scan_unmanaged_project_files(root: Path) -> list[Installation]:
    installations: list[Installation] = []
    central = (root / BASELINE).resolve(strict=False)
    for tool, actions in project_targets(root).items():
        target = actions[0][1]
        if target.is_symlink() or not target.is_file():
            continue
        if target.resolve(strict=False) == central:
            continue
        try:
            baseline = read_baseline(target)
        except (OSError, ValueError):
            continue
        installations.append(
            Installation("unmanaged", root, target, baseline, (tool,))
        )
    return installations


def scan_user(home: Path, user_entry: object = None) -> list[Installation]:
    targets = user_targets(home)
    sources: dict[Path, set[str]] = {}

    claude_link = targets["claude"][0][1]
    if claude_link.is_symlink():
        source = claude_link.resolve(strict=False)
        if _import_contains(targets["claude"][1][1], source):
            sources.setdefault(source, set()).add("claude")

    codex_link = targets["codex"][0][1]
    if codex_link.is_symlink():
        source = codex_link.resolve(strict=False)
        sources.setdefault(source, set()).add("codex")

    managed_path = user_source(home)
    managed = managed_path.resolve(strict=False)
    managed_is_regular = managed_path.is_file() and not managed_path.is_symlink()
    if isinstance(user_entry, dict) and managed not in sources and managed_is_regular:
        sources[managed] = set()

    installations: list[Installation] = []
    for source, tools in sources.items():
        if not source.is_file():
            continue
        try:
            baseline = read_baseline(source)
        except (OSError, ValueError):
            continue
        is_managed = managed_is_regular and source == managed
        installations.append(
            Installation(
                "user" if is_managed else "legacy-user",
                home,
                source,
                baseline,
                tuple(tool for tool in TOOLS if tool in tools),
                _entry_digest(user_entry) if is_managed else None,
            )
        )

    seen = {item.source.resolve(strict=False) for item in installations}
    claude_file = targets["claude"][0][1]
    if (
        claude_file.is_file()
        and not claude_file.is_symlink()
        and claude_file.resolve(strict=False) not in seen
        and _import_contains(targets["claude"][1][1], claude_file)
    ):
        try:
            baseline = read_baseline(claude_file)
        except (OSError, ValueError):
            pass
        else:
            installations.append(
                Installation("unmanaged", home, claude_file, baseline, ("claude",))
            )
            seen.add(claude_file.resolve(strict=False))

    codex_file = targets["codex"][0][1]
    if (
        codex_file.is_file()
        and not codex_file.is_symlink()
        and codex_file.resolve(strict=False) not in seen
    ):
        try:
            baseline = read_baseline(codex_file)
        except (OSError, ValueError):
            pass
        else:
            installations.append(
                Installation("unmanaged", home, codex_file, baseline, ("codex",))
            )
    return installations


def discover_installations(
    home: Path,
    registry: dict[str, object],
    current_root: Path | None = None,
) -> list[Installation]:
    user_entry = registry.get("user")
    installations = scan_user(home, user_entry if isinstance(user_entry, dict) else {})
    projects = registry.get("projects", {})
    if not isinstance(projects, dict):
        return installations
    for value, entry in list(projects.items())[:MAX_PROJECTS]:
        if not isinstance(value, str) or len(value) > 4096:
            continue
        root = Path(value)
        if not root.is_absolute() or root == Path(root.anchor) or not root.is_dir():
            continue
        installation = scan_project(root, entry)
        if installation:
            installations.append(installation)
        installations.extend(scan_unmanaged_project_files(root))

    if current_root is not None:
        current_root = current_root.resolve()
        current_entry = projects.get(str(current_root))
        installation = scan_project(
            current_root,
            current_entry if isinstance(current_entry, dict) else {},
        )
        current_items = ([installation] if installation else [])
        current_items.extend(scan_unmanaged_project_files(current_root))
        seen = {
            item.source.resolve(strict=False)
            for item in installations
        }
        for item in current_items:
            source = item.source.resolve(strict=False)
            if source not in seen:
                installations.append(item)
                seen.add(source)
    return installations


def record_installation(
    registry: dict[str, object], installation: Installation, *, trusted: bool
) -> None:
    previous: object = None
    if installation.kind == "project":
        projects = registry.get("projects", {})
        if isinstance(projects, dict):
            previous = projects.get(str(installation.root.resolve()))
    elif installation.kind in {"user", "legacy-user"}:
        previous = registry.get("user")
    previous_tools = previous.get("tools", []) if isinstance(previous, dict) else []
    tools = [
        tool
        for tool in TOOLS
        if tool in installation.tools or tool in previous_tools
    ]
    entry = {
        "baseline_id": installation.baseline.baseline_id,
        "sha256": installation.baseline.digest if trusted else None,
        "tools": tools,
    }
    if installation.kind == "project":
        projects = registry.setdefault("projects", {})
        if isinstance(projects, dict):
            projects[str(installation.root.resolve())] = entry
    elif installation.kind in {"user", "legacy-user"}:
        registry["user"] = entry


def _backup_path(path: Path) -> Path:
    candidate = path.with_name(f"{path.name}.bak")
    for number in range(1, 101):
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        candidate = path.with_name(f"{path.name}.bak.{number}")
    raise ValueError("too many backup files")


def _atomic_symlink(target: Path, source: Path) -> None:
    temporary = target.with_name(f".{target.name}.aisec-{secrets.token_hex(8)}")
    try:
        temporary.symlink_to(str(source))
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _replace_import(target: Path, old_source: Path, new_source: Path) -> bool:
    if target.is_symlink() or not target.is_file():
        return False
    try:
        content = read_limited(target, MAX_INSTRUCTION_BYTES).decode("utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    old_line, new_line = f"@{old_source}", f"@{new_source}"
    lines = content.splitlines()
    if new_line in lines:
        return True
    if old_line not in lines:
        return False
    replaced = [new_line if line == old_line else line for line in lines]
    trailing = "\n" if content.endswith("\n") else ""
    _atomic_replace(target, ("\n".join(replaced) + trailing).encode())
    return True


def migrate_legacy_user(
    installation: Installation, available: Baseline
) -> tuple[list[str], Installation | None]:
    report: list[str] = []
    home = installation.root
    destination = user_source(home)
    if destination.is_symlink():
        return [f"blocked {destination}: is a symlink"], None
    if destination.exists():
        try:
            existing = read_baseline(destination)
        except (OSError, ValueError):
            return [f"blocked {destination}: is not a valid baseline"], None
        if existing.digest != available.digest:
            return [f"blocked {destination}: contains a different baseline"], None
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_new(destination, available.content)
        report.append(f"added {destination}")

    targets = user_targets(home)
    migrated: list[str] = []
    for tool in installation.tools:
        complete = True
        for kind, target in targets[tool]:
            if kind == "link":
                complete = complete and (
                    _link_points_to(target, destination)
                    or _link_points_to(target, installation.source)
                )
            else:
                complete = complete and not target.is_symlink() and (
                    _import_contains(target, destination)
                    or _import_contains(target, installation.source)
                )
        if not complete:
            report.append(f"blocked {TOOL_LABELS[tool]}: changed since discovery")
            continue
        for kind, target in targets[tool]:
            if kind == "link":
                if _link_points_to(target, destination):
                    continue
                _atomic_symlink(target, destination)
                report.append(f"linked {target} -> {destination}")
            elif not _replace_import(target, installation.source, destination):
                report.append(f"blocked {target}: import changed since discovery")
                complete = False
        if complete:
            migrated.append(tool)

    if not migrated:
        return report, None
    baseline = read_baseline(destination)
    result = Installation(
        "user", home, destination, baseline, tuple(migrated), baseline.digest
    )
    return report, result


def update_installation(
    installation: Installation,
    available: Baseline,
    confirm: Callable[[str, bool], bool],
) -> tuple[list[str], Installation | None]:
    if not installation.baseline.is_official:
        return [f"skipped {installation.label}: customized baseline"], None
    if installation.kind == "legacy-user":
        return migrate_legacy_user(installation, available)
    if installation.kind not in {"project", "user"}:
        return [f"skipped {installation.label}: not managed by this installer"], None
    if installation.source.is_symlink() or not installation.source.is_file():
        return [f"blocked {installation.source}: source is not a regular file"], None
    try:
        current = read_baseline(installation.source)
    except (OSError, ValueError):
        return [f"blocked {installation.source}: source changed since discovery"], None
    if current.digest != installation.baseline.digest:
        return [f"blocked {installation.source}: source changed since discovery"], None

    report: list[str] = []
    if installation.tracked_digest != installation.baseline.digest:
        question = (
            f"{installation.label} was not installed by this setup or changed locally. "
            "Back it up and replace it?"
        )
        if not confirm(question, False):
            return [f"skipped {installation.label}: kept local content"], None
        backup = _backup_path(installation.source)
        _write_new(backup, installation.baseline.content)
        report.append(f"backed up {installation.source} to {backup}")

    _atomic_replace(installation.source, available.content)
    if installation.baseline.version == available.version:
        report.append(
            f"replaced differing {installation.baseline.baseline_id} content "
            f"in {installation.source}"
        )
    else:
        report.append(
            f"updated {installation.source}: "
            f"{installation.baseline.version} -> {available.version}"
        )
    baseline = read_baseline(installation.source)
    return report, Installation(
        installation.kind,
        installation.root,
        installation.source,
        baseline,
        installation.tools,
        baseline.digest,
    )


def _read_answer(input_fn: Callable[[str], str], prompt: str) -> str:
    answer = input_fn(prompt)
    if len(answer) > 4096:
        raise ValueError("input is too long")
    return answer.strip()


def ask_yes_no(
    input_fn: Callable[[str], str], question: str, default: bool
) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    for _ in range(3):
        answer = _read_answer(input_fn, question + suffix).lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
    return default


def choose_tools(
    input_fn: Callable[[str], str],
    output: Callable[[str], None],
    tools: tuple[str, ...],
) -> list[str] | None:
    output("\nChoose tools (press Enter for all):")
    for number, tool in enumerate(tools, 1):
        output(f"  {number}. {TOOL_LABELS[tool]}")
    for _ in range(3):
        answer = _read_answer(input_fn, "Tools: ")
        if not answer or answer.lower() == "all":
            return list(tools)
        chosen: list[str] = []
        valid = True
        for item in re.split(r"[\s,]+", answer.lower()):
            if item.isdigit() and 1 <= int(item) <= len(tools):
                tool = tools[int(item) - 1]
            elif item in tools:
                tool = item
            else:
                valid = False
                break
            if tool not in chosen:
                chosen.append(tool)
        if valid and chosen:
            return chosen
        output("Invalid selection. Use numbers or tool names separated by commas.")
    return None


def _path_from_answer(answer: str, home: Path) -> Path:
    if answer == "~":
        candidate = home
    elif answer.startswith("~/"):
        candidate = home / answer[2:]
    else:
        candidate = Path(answer)
    return candidate.resolve()


def _installation_state(installation: Installation, available: Baseline) -> str:
    if not installation.baseline.is_official:
        return "customized; automatic update disabled"
    if installation.kind == "unmanaged":
        return "manual file; automatic update disabled"
    if installation.has_update(available):
        if installation.baseline.version < available.version:
            state = f"update to {available.baseline_id} available"
        else:
            state = f"content differs from available {available.baseline_id}"
        if (
            installation.kind in {"project", "user"}
            and installation.tracked_digest != installation.baseline.digest
        ):
            state += "; replacement needs separate confirmation and a backup"
        return state
    if installation.baseline.version > available.version:
        return "newer than the available baseline"
    if installation.kind == "legacy-user":
        return "version matches; migration to managed storage recommended"
    if available.origin.startswith("GitHub release "):
        return "current published version"
    return "matches the bundled baseline"


def _installation_line(
    installation: Installation,
    available: Baseline,
    *,
    include_label: bool,
) -> str:
    tools = (
        ", ".join(TOOL_LABELS[tool] for tool in installation.tools)
        or "no tool integrations"
    )
    if include_label:
        label = installation.label
    elif installation.kind == "unmanaged":
        label = f"manual file {display_path(installation.source)}"
    elif installation.kind == "project":
        label = "project baseline"
    elif installation.kind == "legacy-user":
        label = f"checkout-linked baseline {display_path(installation.source)}"
    else:
        label = "managed user baseline"
    return (
        f"  - {label}: {installation.baseline.baseline_id} — "
        f"{_installation_state(installation, available)} ({tools})"
    )


def _show_installations(
    output: Callable[[str], None],
    installations: list[Installation],
    available: Baseline,
    heading: str,
) -> None:
    output(heading)
    if not installations:
        output("  - no baseline found")
        return
    for installation in installations:
        output(_installation_line(installation, available, include_label=True))


def _show_setup_status(
    output: Callable[[str], None],
    installations: list[Installation],
    available: Baseline,
    home: Path,
    current_root: Path,
) -> None:
    current_resolved = current_root.resolve(strict=False)
    home_resolved = home.resolve(strict=False)
    current: list[Installation] = []
    user: list[Installation] = []
    other: list[Installation] = []
    for installation in installations:
        root = installation.root.resolve(strict=False)
        if installation.kind in {"user", "legacy-user"}:
            user.append(installation)
        elif installation.kind == "unmanaged" and root == home_resolved:
            user.append(installation)
        elif root == current_resolved:
            current.append(installation)
        else:
            other.append(installation)

    output("\nInstallation status")
    output(f"\nCurrent project {display_path(current_root)}:")
    if not any(item.kind == "project" for item in current):
        output("  - no managed project installation")
    for installation in current:
        output(_installation_line(installation, available, include_label=False))

    output("\nUser-wide:")
    if not any(item.kind in {"user", "legacy-user"} for item in user):
        output("  - no managed user installation")
    for installation in user:
        output(_installation_line(installation, available, include_label=False))

    if other:
        output("\nOther known projects:")
        for installation in other:
            output(_installation_line(installation, available, include_label=True))


def _record_current_scope(
    registry: dict[str, object],
    installation: Installation | None,
    available: Baseline,
) -> None:
    if not installation:
        return
    trusted = (
        installation.baseline.digest == available.digest
        or installation.tracked_digest == installation.baseline.digest
    )
    record_installation(registry, installation, trusted=trusted)


def _update_key(installation: Installation) -> Path:
    return installation.source.resolve(strict=False)


def _review_updates(
    installations: list[Installation],
    available: Baseline,
    registry: dict[str, object],
    reviewed: set[Path],
    input_fn: Callable[[str], str],
    output: Callable[[str], None],
) -> bool:
    outdated = [
        item
        for item in installations
        if item.has_update(available) and _update_key(item) not in reviewed
    ]
    if not outdated:
        return False

    output("\nUpdates available")
    changed = False
    for installation in outdated:
        reviewed.add(_update_key(installation))
        if installation.baseline.version < available.version:
            question = (
                f"Update {installation.label} from "
                f"{installation.baseline.baseline_id} to {available.baseline_id}?"
            )
        else:
            question = (
                f"Replace the differing {installation.baseline.baseline_id} content "
                f"in {installation.label} with the available copy?"
            )
        if not ask_yes_no(input_fn, question, True):
            output(f"kept {installation.label} unchanged")
            continue
        report, updated = update_installation(
            installation,
            available,
            lambda prompt, default: ask_yes_no(input_fn, prompt, default),
        )
        for line in report:
            output(line)
        if updated:
            record_installation(registry, updated, trusted=True)
            changed = True
    return changed


def _install_project_interactively(
    home: Path,
    registry: dict[str, object],
    available: Baseline,
    reviewed_updates: set[Path],
    input_fn: Callable[[str], str],
    output: Callable[[str], None],
    root: Path | None = None,
) -> bool:
    if root is None:
        answer = _read_answer(input_fn, "Project directory (blank to cancel): ")
        if not answer:
            return False
        try:
            root = _path_from_answer(answer, home)
        except (OSError, RuntimeError):
            output("Invalid project path.")
            return False
    else:
        root = root.resolve()
    if root == Path(root.anchor) or not root.is_dir():
        output("Project directory must be an existing non-root directory.")
        return False

    projects = registry.get("projects", {})
    entry = projects.get(str(root)) if isinstance(projects, dict) else None
    existing = scan_project(root, entry if isinstance(entry, dict) else {})
    unmanaged = scan_unmanaged_project_files(root)
    found = ([existing] if existing else []) + unmanaged
    _show_installations(
        output,
        found,
        available,
        f"\nSelected project {display_path(root)}:",
    )
    changed = _review_updates(
        found,
        available,
        registry,
        reviewed_updates,
        input_fn,
        output,
    )

    tools = choose_tools(input_fn, output, TOOLS)
    if not tools:
        output("Setup cancelled.")
        return changed
    for line in install(tools, root, None, content=available.content):
        output(line)
    projects = registry.get("projects", {})
    entry = projects.get(str(root)) if isinstance(projects, dict) else None
    installed = scan_project(root, entry if isinstance(entry, dict) else {})
    _record_current_scope(registry, installed, available)
    return changed or installed is not None


def _install_user_interactively(
    home: Path,
    registry: dict[str, object],
    available: Baseline,
    reviewed_updates: set[Path],
    input_fn: Callable[[str], str],
    output: Callable[[str], None],
) -> bool:
    user_entry = registry.get("user")
    existing = scan_user(home, user_entry if isinstance(user_entry, dict) else {})
    _show_installations(output, existing, available, "\nSelected user-wide scope:")
    changed = _review_updates(
        existing,
        available,
        registry,
        reviewed_updates,
        input_fn,
        output,
    )
    user_entry = registry.get("user")
    existing = scan_user(home, user_entry if isinstance(user_entry, dict) else {})
    legacy = [
        item
        for item in existing
        if item.kind == "legacy-user" and _update_key(item) not in reviewed_updates
    ]
    if legacy and ask_yes_no(
        input_fn, "Move checkout-linked user installation to managed storage?", True
    ):
        for installation in legacy:
            reviewed_updates.add(_update_key(installation))
            report, migrated = migrate_legacy_user(installation, available)
            for line in report:
                output(line)
            if migrated:
                record_installation(registry, migrated, trusted=True)
                changed = True

    tools = choose_tools(input_fn, output, ("claude", "codex"))
    if not tools:
        output("Setup cancelled.")
        return changed
    for line in install(tools, Path.cwd(), home, content=available.content):
        output(line)
    user_entry = registry.get("user")
    managed = [
        item
        for item in scan_user(
            home, user_entry if isinstance(user_entry, dict) else {}
        )
        if item.kind == "user"
    ]
    if managed:
        _record_current_scope(registry, managed[0], available)
        return True
    return changed


def _save_setup_registry(
    state_path: Path,
    registry: dict[str, object],
    registry_writable: bool,
    output: Callable[[str], None],
) -> None:
    if registry_writable:
        save_registry(state_path, registry)
    else:
        output("Changes completed, but the invalid registry was not overwritten.")


def interactive_setup(
    *,
    home: Path,
    input_fn: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    check_online: bool = True,
    state_path: Path | None = None,
    current_root: Path | None = None,
) -> int:
    available, online_note = latest_available(check_online)
    state_path = state_path or registry_path(home)
    registry, registry_writable, registry_note = load_registry(state_path)
    current_root = (current_root or Path.cwd()).resolve()
    if current_root == Path(current_root.anchor) or not current_root.is_dir():
        raise ValueError("current project must be an existing non-root directory")

    output("AI Secure Coding Baseline setup")
    output(f"Available: {available.baseline_id} ({available.origin})")
    output(online_note)
    if registry_note:
        output(registry_note)
    installations = discover_installations(home, registry, current_root)
    _show_setup_status(output, installations, available, home, current_root)

    reviewed_updates: set[Path] = set()
    changed = _review_updates(
        installations,
        available,
        registry,
        reviewed_updates,
        input_fn,
        output,
    )
    if changed:
        _save_setup_registry(state_path, registry, registry_writable, output)

    current_installed = any(
        item.kind == "project"
        and item.root.resolve(strict=False) == current_root.resolve(strict=False)
        for item in installations
    )
    user_installed = any(item.kind in {"user", "legacy-user"} for item in installations)
    current_action = "Check or add tools in" if current_installed else "Install in"
    user_action = "Check or add tools for" if user_installed else "Install for"
    output("\nNext action")
    output(f"  1. {current_action} current project {display_path(current_root)}")
    output("  2. Install or check another project")
    output(f"  3. {user_action} this user")
    output("  4. Exit")
    choice = ""
    for _ in range(3):
        choice = _read_answer(input_fn, "Choice [4]: ") or "4"
        if choice in {"1", "2", "3", "4"}:
            break
        output("Invalid selection. Choose 1, 2, 3, or 4.")
    else:
        output("Invalid selection; no additional changes made.")
        return 2

    action_changed = False
    if choice == "1":
        action_changed = _install_project_interactively(
            home,
            registry,
            available,
            reviewed_updates,
            input_fn,
            output,
            current_root,
        )
    elif choice == "2":
        action_changed = _install_project_interactively(
            home, registry, available, reviewed_updates, input_fn, output
        )
    elif choice == "3":
        action_changed = _install_user_interactively(
            home, registry, available, reviewed_updates, input_fn, output
        )

    if action_changed:
        _save_setup_registry(state_path, registry, registry_writable, output)
    if choice == "4":
        output("Setup complete." if changed else "No changes made.")
    return 0


def _register_noninteractive(
    registry: dict[str, object], root: Path, home: Path | None
) -> None:
    available = bundled_baseline()
    if home is None:
        installation = scan_project(root, {})
    else:
        matches = [item for item in scan_user(home, {}) if item.kind == "user"]
        installation = matches[0] if matches else None
    if installation:
        trusted = installation.baseline.digest == available.digest
        record_installation(registry, installation, trusted=trusted)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "tools", nargs="*", help=f"any of {', '.join(TOOLS)}; default is all"
    )
    parser.add_argument(
        "--user", action="store_true", help="install for this user instead of a project"
    )
    parser.add_argument(
        "--into",
        type=Path,
        default=Path.cwd(),
        help="project directory (default: the current one)",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="run the guided setup and updater"
    )
    parser.add_argument(
        "--offline", action="store_true", help="skip the release check during setup"
    )
    args = parser.parse_args(argv)

    if args.interactive:
        if args.tools or args.user:
            parser.error("--interactive cannot be combined with tools or --user")
        if not sys.stdin.isatty():
            parser.error("interactive setup requires a terminal; use make install in scripts")
        try:
            return interactive_setup(home=Path.home(), check_online=not args.offline)
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.", file=sys.stderr)
            return 130
        except (OSError, ValueError):
            print("Setup stopped after an error; review the reported files.", file=sys.stderr)
            return 1

    if args.offline:
        parser.error("--offline is only valid with --interactive")
    tools = list(args.tools) or list(TOOLS)
    unknown = [tool for tool in tools if tool not in TOOLS]
    if unknown:
        parser.error(f"unknown tool {unknown[0]!r}; choose from {', '.join(TOOLS)}")

    root = args.into.resolve()
    if not args.user and (root == Path(root.anchor) or not root.is_dir()):
        parser.error("--into must be an existing non-root directory")
    home = Path.home() if args.user else None
    for line in install(tools, root, home):
        print(line)

    state_path = registry_path(Path.home())
    registry, writable, note = load_registry(state_path)
    if note:
        print(note, file=sys.stderr)
    if writable:
        _register_noninteractive(registry, root, home)
        save_registry(state_path, registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
