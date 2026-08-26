#!/usr/bin/env python3
"""Install, inspect, and safely update the baseline from its official upstream."""

import argparse
import base64
import hashlib
import json
import os
import re
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

BASELINE = "secure-coding-baseline.md"
TOOLS = ("claude", "codex", "copilot")
OFFICIAL_NAME = "aisec"
UPSTREAM_REPOSITORY = "appsec-foundry/ai-secure-coding-baseline"
UPSTREAM_URL = f"https://github.com/{UPSTREAM_REPOSITORY}"
API_ROOT = f"https://api.github.com/repos/{UPSTREAM_REPOSITORY}"
LATEST_RELEASE_URL = f"{API_ROOT}/releases/latest"
REPOSITORY_URL = API_ROOT
MAIN_BRANCH_URL = f"{API_ROOT}/branches/main"
CONTENTS_URL = f"{API_ROOT}/contents/{BASELINE}"
TAG_REF_URL = f"{API_ROOT}/git/ref/tags"
TAG_OBJECT_URL = f"{API_ROOT}/git/tags"

API_VERSION = "2026-03-10"
ONLINE_TIMEOUT = 6
MAX_API_BYTES = 512 * 1024
MAX_BASELINE_BYTES = 256 * 1024
MAX_INSTRUCTION_BYTES = 512 * 1024

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
RELEASE_TAG_RE = re.compile(rf"^(?:v|{OFFICIAL_NAME}-)?(?P<version>{SEMVER_TEXT})$")
SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


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
        if any(
            item.isdigit() and len(item) > 1 and item.startswith("0")
            for item in prerelease
        ):
            raise ValueError(
                "numeric prerelease identifiers cannot have leading zeroes"
            )
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
    source_url: str

    @property
    def baseline_id(self) -> str:
        return f"{self.name}-{self.version}"

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()

    @property
    def is_official(self) -> bool:
        return self.name == OFFICIAL_NAME and not self.version.metadata


def display_path(path: Path) -> str:
    """Quote paths so control characters cannot alter terminal output."""
    return repr(str(path))


def parse_baseline(content: bytes, origin: str, source_url: str) -> Baseline:
    if not content or len(content) > MAX_BASELINE_BYTES:
        raise ValueError("baseline content has an invalid size")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("baseline content is not UTF-8") from error
    matches = list(BASELINE_ID_RE.finditer(text))
    if len(matches) != 1:
        raise ValueError("expected exactly one baseline-id")
    if not content.startswith(b"# AI Secure Coding Baseline\n"):
        raise ValueError("baseline content has an unexpected format")
    match = matches[0]
    baseline = Baseline(
        match.group("name"),
        SemVer.parse(match.group("version")),
        content,
        origin,
        source_url,
    )
    if not baseline.is_official:
        raise ValueError("upstream did not provide the official baseline")
    return baseline


def read_limited(path: Path, limit: int) -> bytes:
    with path.open("rb") as handle:
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise ValueError("file is too large")
    return content


def read_local_baseline(path: Path) -> Baseline:
    return parse_baseline(
        read_limited(path, MAX_INSTRUCTION_BYTES), str(path), str(path)
    )


class _GitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        destination = urllib.parse.urlsplit(new_url)
        if destination.scheme != "https" or destination.netloc != "api.github.com":
            raise urllib.error.HTTPError(
                new_url,
                code,
                "refused cross-host upstream redirect",
                headers,
                file_pointer,
            )
        return super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )


def _read_json_url(url: str) -> object:
    destination = urllib.parse.urlsplit(url)
    allowed_prefix = f"/repos/{UPSTREAM_REPOSITORY}/"
    if (
        destination.scheme != "https"
        or destination.netloc != "api.github.com"
        or not (
            destination.path == allowed_prefix[:-1]
            or destination.path.startswith(allowed_prefix)
        )
    ):
        raise ValueError("unexpected upstream server or repository")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "secure-coding-baseline-installer",
            "X-GitHub-Api-Version": API_VERSION,
        },
    )
    opener = urllib.request.build_opener(_GitHubRedirectHandler())
    with opener.open(request, timeout=ONLINE_TIMEOUT) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if (
            final.scheme != "https"
            or final.netloc != "api.github.com"
            or not (
                final.path == allowed_prefix[:-1]
                or final.path.startswith(allowed_prefix)
            )
        ):
            raise ValueError("unexpected upstream response location")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_API_BYTES:
            raise ValueError("upstream response is too large")
        payload = response.read(MAX_API_BYTES + 1)
    if len(payload) > MAX_API_BYTES:
        raise ValueError("upstream response is too large")
    return json.loads(payload.decode("utf-8"))


def _commit_sha(value: object) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ValueError("upstream did not provide a valid commit identifier")
    return value


def _resolve_tag_commit(tag: str, fetch_json: Callable[[str], object]) -> str:
    encoded_tag = urllib.parse.quote(tag, safe="")
    payload = fetch_json(f"{TAG_REF_URL}/{encoded_tag}")
    if not isinstance(payload, dict) or not isinstance(payload.get("object"), dict):
        raise ValueError("release tag reference is invalid")
    target = payload["object"]
    for _ in range(4):
        target_type = target.get("type")
        sha = _commit_sha(target.get("sha"))
        if target_type == "commit":
            return sha
        if target_type != "tag":
            raise ValueError("release tag has an unsupported target")
        tag_object = fetch_json(f"{TAG_OBJECT_URL}/{sha}")
        if not isinstance(tag_object, dict) or not isinstance(
            tag_object.get("object"), dict
        ):
            raise ValueError("annotated release tag is invalid")
        target = tag_object["object"]
    raise ValueError("release tag nesting is too deep")


def _decode_contents(payload: object, commit: str, origin: str) -> Baseline:
    if not isinstance(payload, dict) or payload.get("type") != "file":
        raise ValueError("upstream baseline is not a file")
    if payload.get("encoding") != "base64" or not isinstance(
        payload.get("content"), str
    ):
        raise ValueError("upstream baseline has an unsupported encoding")
    try:
        encoded = "".join(payload["content"].splitlines())
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("upstream baseline is not valid base64") from error
    source_url = f"{UPSTREAM_URL}/blob/{commit}/{BASELINE}"
    return parse_baseline(content, origin, source_url)


def _fetch_contents(
    commit: str, origin: str, fetch_json: Callable[[str], object]
) -> Baseline:
    query = urllib.parse.urlencode({"ref": commit})
    return _decode_contents(fetch_json(f"{CONTENTS_URL}?{query}"), commit, origin)


def fetch_available(
    fetch_json: Callable[[str], object] = _read_json_url,
) -> Baseline:
    try:
        release = fetch_json(LATEST_RELEASE_URL)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    else:
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
        expected_version = SemVer.parse(tag_match.group("version"))
        commit = _resolve_tag_commit(tag, fetch_json)
        baseline = _fetch_contents(
            commit, f"GitHub release {tag} at {commit[:12]}", fetch_json
        )
        if baseline.version != expected_version:
            raise ValueError("release tag and baseline-id do not match")
        return baseline

    repository = fetch_json(REPOSITORY_URL)
    if (
        not isinstance(repository, dict)
        or repository.get("full_name") != UPSTREAM_REPOSITORY
        or repository.get("default_branch") != "main"
        or repository.get("archived") is True
        or repository.get("disabled") is True
    ):
        raise ValueError("canonical upstream repository metadata is invalid")
    branch = fetch_json(MAIN_BRANCH_URL)
    if not isinstance(branch, dict) or not isinstance(branch.get("commit"), dict):
        raise ValueError("canonical upstream main branch is invalid")
    commit = _commit_sha(branch["commit"].get("sha"))
    return _fetch_contents(commit, f"GitHub main snapshot at {commit[:12]}", fetch_json)


def project_source(root: Path) -> Path:
    return root / BASELINE


def user_source(home: Path) -> Path:
    return home / ".local" / "share" / "ai-secure-coding-baseline" / BASELINE


def project_targets(root: Path) -> dict[str, tuple[str, Path]]:
    return {
        "claude": ("link", root / ".claude" / "rules" / BASELINE),
        "codex": ("link", root / "AGENTS.md"),
        "copilot": ("link", root / ".github" / "copilot-instructions.md"),
    }


def user_targets(home: Path) -> dict[str, tuple[tuple[str, Path], ...]]:
    return {
        "claude": (
            ("link", home / ".claude" / BASELINE),
            ("import", home / ".claude" / "CLAUDE.md"),
        ),
        "codex": (("link", home / ".codex" / "AGENTS.md"),),
        "copilot": (),
    }


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


def _backup_path(path: Path) -> Path:
    candidate = path.with_name(f"{path.name}.bak")
    for number in range(1, 101):
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        candidate = path.with_name(f"{path.name}.bak.{number}")
    raise ValueError("too many backup files")


def _link_points_to(target: Path, source: Path) -> bool:
    return target.is_symlink() and target.resolve(strict=False) == source.resolve(
        strict=False
    )


def _has_safe_parent(path: Path, boundary: Path) -> bool:
    boundary = boundary.resolve()
    candidate = path.absolute()
    try:
        relative = candidate.relative_to(boundary)
    except ValueError:
        return False
    current = boundary
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return False
    return True


def _install_link(target: Path, source: Path, *, relative: bool, boundary: Path) -> str:
    if _link_points_to(target, source):
        return f"in place {target}"
    if target.exists() or target.is_symlink():
        return f"blocked {target}: exists and was left untouched"
    if not _has_safe_parent(target, boundary):
        return f"blocked {target}: parent path leaves the selected scope"
    target.parent.mkdir(parents=True, exist_ok=True)
    link = os.path.relpath(source, target.parent) if relative else str(source)
    target.symlink_to(link)
    return f"linked {target} -> {link}"


def _install_import(target: Path, source: Path, *, boundary: Path) -> str:
    line = f"@{source}"
    if target.exists() or target.is_symlink():
        if target.is_file() and not target.is_symlink():
            try:
                existing = read_limited(target, MAX_INSTRUCTION_BYTES).decode("utf-8")
            except (OSError, UnicodeDecodeError, ValueError):
                existing = ""
            if line in existing.splitlines():
                return f"in place {target}"
        return f"blocked {target}: exists; add {line!r} manually"
    if not _has_safe_parent(target, boundary):
        return f"blocked {target}: parent path leaves the selected scope"
    _write_new(target, f"{line}\n".encode())
    return f"wrote {target}"


def _integration_state(
    source: Path,
    targets: dict[str, tuple[tuple[str, Path], ...]],
    tools: list[str],
) -> list[str]:
    report: list[str] = []
    for tool in tools:
        actions = targets[tool]
        if not actions:
            report.append(f"  {tool}: no supported user-wide target")
            continue
        matched = True
        for kind, target in actions:
            if kind == "link":
                matched = matched and _link_points_to(target, source)
            else:
                line = f"@{source}"
                try:
                    matched = (
                        matched
                        and line
                        in read_limited(target, MAX_INSTRUCTION_BYTES)
                        .decode("utf-8")
                        .splitlines()
                    )
                except (OSError, UnicodeDecodeError, ValueError):
                    matched = False
        report.append(f"  {tool}: {'installed' if matched else 'not installed'}")
    return report


def status(source: Path, available: Baseline) -> tuple[str, Baseline | None]:
    if source.is_symlink():
        return "blocked: baseline source is a symlink", None
    if not source.exists():
        return "not installed", None
    if not source.is_file():
        return "blocked: baseline source is not a regular file", None
    try:
        local = read_local_baseline(source)
    except (OSError, ValueError):
        return "blocked: local file is not a valid official baseline", None
    if local.digest == available.digest:
        return "current", local
    if local.version < available.version:
        return (
            f"update available: {local.baseline_id} -> {available.baseline_id}",
            local,
        )
    if local.version == available.version:
        return "local content differs from upstream at the same version", local
    return f"local {local.baseline_id} is newer than upstream", local


def install_baseline(
    source: Path, available: Baseline, *, boundary: Path | None = None
) -> list[str]:
    state, local = status(source, available)
    if local is not None and local.digest == available.digest:
        return [f"in place {source}"]
    if source.exists() or source.is_symlink():
        return [f"blocked {source}: {state}; use update after reviewing it"]
    if not _has_safe_parent(source, boundary or source.parent):
        return [f"blocked {source}: parent path leaves the selected scope"]
    _write_new(source, available.content)
    return [f"installed {available.baseline_id} at {source}"]


def update_baseline(
    source: Path,
    available: Baseline,
    *,
    replace_same_version: bool,
    boundary: Path | None = None,
) -> list[str]:
    state, local = status(source, available)
    if local is None:
        return [f"blocked {source}: {state}; install it first"]
    if local.digest == available.digest:
        return [f"current {source}"]
    if local.version > available.version:
        return [f"blocked {source}: {state}"]
    if local.version == available.version and not replace_same_version:
        return [
            f"blocked {source}: {state}; rerun with --backup-and-replace "
            "only after reviewing the local difference"
        ]
    if not _has_safe_parent(source, boundary or source.parent):
        return [f"blocked {source}: parent path leaves the selected scope"]
    backup = _backup_path(source)
    _write_new(backup, local.content)
    _atomic_replace(source, available.content)
    return [
        f"backed up {source} to {backup}",
        f"updated {source}: {local.baseline_id} -> {available.baseline_id}",
    ]


def install_integrations(
    source: Path,
    targets: dict[str, tuple[tuple[str, Path], ...]],
    tools: list[str],
    *,
    relative: bool,
    boundary: Path | None = None,
) -> list[str]:
    report: list[str] = []
    boundary = boundary or source.parent
    for tool in tools:
        actions = targets[tool]
        if not actions:
            report.append(f"skipped {tool}: no supported user-wide target")
            continue
        for kind, target in actions:
            if kind == "link":
                report.append(
                    _install_link(target, source, relative=relative, boundary=boundary)
                )
            else:
                report.append(_install_import(target, source, boundary=boundary))
    return report


def _scope(args: argparse.Namespace) -> tuple[Path, dict, bool, Path]:
    if args.user:
        home = Path.home().resolve()
        return user_source(home), user_targets(home), False, home
    root = args.into.resolve()
    if root == Path(root.anchor) or not root.is_dir():
        raise ValueError("--into must be an existing non-root directory")
    targets = {tool: (action,) for tool, action in project_targets(root).items()}
    return project_source(root), targets, True, root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "install", "update"))
    parser.add_argument(
        "tools",
        nargs="*",
        metavar="TOOL",
        help=f"any of {', '.join(TOOLS)}; default is every supported tool",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--user", action="store_true", help="use user-wide locations")
    scope.add_argument(
        "--into",
        type=Path,
        default=Path.cwd(),
        help="project directory (default: current directory)",
    )
    parser.add_argument(
        "--backup-and-replace",
        action="store_true",
        help="replace differing same-version content after making a backup",
    )
    args = parser.parse_args(argv)
    if args.backup_and_replace and args.action != "update":
        parser.error("--backup-and-replace is valid only with update")
    unknown = [tool for tool in args.tools if tool not in TOOLS]
    if unknown:
        parser.error(f"unknown tool {unknown[0]!r}; choose from {', '.join(TOOLS)}")
    tools = list(args.tools) or list(TOOLS if not args.user else ("claude", "codex"))
    if args.user and "copilot" in tools:
        parser.error("GitHub Copilot has no supported local user-wide target")

    try:
        source, targets, relative, boundary = _scope(args)
        available = fetch_available()
        print(f"Upstream: {UPSTREAM_URL}")
        print(f"Available: {available.baseline_id} ({available.origin})")
        print(f"Source: {available.source_url}")
        local_state, _local = status(source, available)
        print(f"Local {display_path(source)}: {local_state}")

        if args.action == "status":
            for line in _integration_state(source, targets, tools):
                print(line)
            return 0
        if args.action == "install":
            report = install_baseline(source, available, boundary=boundary)
            for line in report:
                print(line)
            if (
                not source.is_file()
                or read_local_baseline(source).digest != available.digest
            ):
                return 1
            for line in install_integrations(
                source,
                targets,
                tools,
                relative=relative,
                boundary=boundary,
            ):
                print(line)
            integration_state = _integration_state(source, targets, tools)
            return (
                0
                if all(line.endswith(": installed") for line in integration_state)
                else 1
            )
        for line in update_baseline(
            source,
            available,
            replace_same_version=args.backup_and_replace,
            boundary=boundary,
        ):
            print(line)
        return (
            0
            if source.is_file()
            and read_local_baseline(source).digest == available.digest
            else 1
        )
    except urllib.error.HTTPError as error:
        print(
            f"Upstream check failed with HTTP {error.code}; no files were changed.",
            file=sys.stderr,
        )
    except (OSError, ValueError, json.JSONDecodeError):
        print(
            "Baseline operation failed safely; no unchecked content was installed.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
