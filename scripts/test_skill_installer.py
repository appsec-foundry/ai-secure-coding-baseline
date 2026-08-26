#!/usr/bin/env python3
"""Check the standalone baseline skill without network access."""

import base64
import contextlib
import importlib.util
import io
import sys
import tempfile
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALLER_PATH = (
    REPO / "skills" / "secure-coding-baseline-installer" / "scripts" / "install.py"
)
spec = importlib.util.spec_from_file_location(
    "baseline_skill_installer", INSTALLER_PATH
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load skill installer")
installer = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = installer
spec.loader.exec_module(installer)

failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if condition:
        print(f"ok: {label}")
    else:
        failures += 1
        print(f"FAIL: {label}{': ' + detail if detail else ''}")


canonical_content = (REPO / installer.BASELINE).read_bytes()
canonical = installer.parse_baseline(
    canonical_content,
    "test upstream",
    f"{installer.UPSTREAM_URL}/blob/test/{installer.BASELINE}",
)

check(
    "the skill pins the canonical upstream repository",
    installer.UPSTREAM_REPOSITORY == "appsec-foundry/ai-secure-coding-baseline"
    and installer.UPSTREAM_URL
    == "https://github.com/appsec-foundry/ai-secure-coding-baseline",
)


def content_payload(content: bytes) -> dict[str, object]:
    return {
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(content).decode(),
    }


main_commit = "a" * 40


def fake_main(url: str) -> object:
    if url == installer.LATEST_RELEASE_URL:
        raise urllib.error.HTTPError(url, 404, "not found", {}, None)
    if url == installer.REPOSITORY_URL:
        return {
            "full_name": installer.UPSTREAM_REPOSITORY,
            "default_branch": "main",
            "archived": False,
            "disabled": False,
        }
    if url == installer.MAIN_BRANCH_URL:
        return {"commit": {"sha": main_commit}}
    if url == f"{installer.CONTENTS_URL}?ref={main_commit}":
        return content_payload(canonical_content)
    raise AssertionError(f"unexpected URL {url}")


main_baseline = installer.fetch_available(fake_main)
check(
    "without a release the skill pins main to a commit before fetching",
    main_baseline.digest == canonical.digest
    and main_commit in main_baseline.source_url
    and main_baseline.origin.endswith(main_commit[:12]),
    main_baseline.source_url,
)


def wrong_repository(url: str) -> object:
    if url == installer.LATEST_RELEASE_URL:
        raise urllib.error.HTTPError(url, 404, "not found", {}, None)
    if url == installer.REPOSITORY_URL:
        return {
            "full_name": "someone-else/ai-secure-coding-baseline",
            "default_branch": "main",
        }
    raise AssertionError(f"unexpected URL {url}")


try:
    installer.fetch_available(wrong_repository)
except ValueError:
    wrong_upstream_rejected = True
else:
    wrong_upstream_rejected = False
check("repository identity mismatches are rejected", wrong_upstream_rejected)

original_fetch_available = installer.fetch_available
installer.fetch_available = lambda: canonical
with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
    cli_status = installer.main(["status", "--into", tmp])
installer.fetch_available = original_fetch_available
check("status accepts the default empty tool selection", cli_status == 0)

release_commit = "b" * 40
release_content = canonical_content.replace(
    canonical.baseline_id.encode(), b"aisec-9.8.7", 1
)


def fake_release(url: str) -> object:
    if url == installer.LATEST_RELEASE_URL:
        return {"tag_name": "v9.8.7", "draft": False, "prerelease": False}
    if url == f"{installer.TAG_REF_URL}/v9.8.7":
        return {"object": {"type": "commit", "sha": release_commit}}
    if url == f"{installer.CONTENTS_URL}?ref={release_commit}":
        return content_payload(release_content)
    raise AssertionError(f"unexpected URL {url}")


release = installer.fetch_available(fake_release)
check(
    "a stable release resolves to an immutable commit",
    str(release.version) == "9.8.7"
    and release_commit in release.source_url
    and release.origin.startswith("GitHub release v9.8.7"),
)


def mismatched_release(url: str) -> object:
    if url == installer.LATEST_RELEASE_URL:
        return {"tag_name": "v9.8.6", "draft": False, "prerelease": False}
    if url == f"{installer.TAG_REF_URL}/v9.8.6":
        return {"object": {"type": "commit", "sha": release_commit}}
    if url == f"{installer.CONTENTS_URL}?ref={release_commit}":
        return content_payload(release_content)
    raise AssertionError(f"unexpected URL {url}")


try:
    installer.fetch_available(mismatched_release)
except ValueError:
    mismatched_version_rejected = True
else:
    mismatched_version_rejected = False
check("release tags must match the baseline ID", mismatched_version_rejected)

try:
    installer._GitHubRedirectHandler().redirect_request(
        None, None, 302, "redirect", {}, "https://example.com/baseline"
    )
except urllib.error.HTTPError:
    redirect_rejected = True
else:
    redirect_rejected = False
check("cross-host redirects are rejected", redirect_rejected)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "project"
    root.mkdir()
    source = installer.project_source(root)
    report = installer.install_baseline(source, canonical)
    targets = {
        tool: (action,) for tool, action in installer.project_targets(root).items()
    }
    report += installer.install_integrations(
        source, targets, list(installer.TOOLS), relative=True
    )
    state, local = installer.status(source, canonical)
    check(
        "project install creates one source and supported tool links",
        state == "current"
        and local is not None
        and (root / "AGENTS.md").is_symlink()
        and (root / ".claude" / "rules" / installer.BASELINE).is_symlink()
        and (root / ".github" / "copilot-instructions.md").is_symlink(),
        str(report),
    )

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = installer.project_source(root)
    old_content = canonical_content.replace(
        canonical.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    source.write_bytes(old_content)
    report = installer.update_baseline(source, canonical, replace_same_version=False)
    check(
        "an older official baseline is backed up before update",
        installer.read_local_baseline(source).digest == canonical.digest
        and (root / f"{installer.BASELINE}.bak").read_bytes() == old_content,
        str(report),
    )

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp) / "home"
    home.mkdir()
    source = installer.user_source(home)
    report = installer.install_baseline(source, canonical, boundary=home)
    report += installer.install_integrations(
        source,
        installer.user_targets(home),
        ["claude", "codex"],
        relative=False,
        boundary=home,
    )
    check(
        "user-wide install uses managed storage and supported instruction targets",
        source.read_bytes() == canonical_content
        and (home / ".claude" / installer.BASELINE).resolve() == source.resolve()
        and f"@{source}" in (home / ".claude" / "CLAUDE.md").read_text().splitlines()
        and (home / ".codex" / "AGENTS.md").resolve() == source.resolve(),
        str(report),
    )

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = installer.project_source(root)
    variation = canonical_content + b"\nlocal variation\n"
    source.write_bytes(variation)
    blocked = installer.update_baseline(source, canonical, replace_same_version=False)
    unchanged = source.read_bytes() == variation
    replaced = installer.update_baseline(source, canonical, replace_same_version=True)
    check(
        "same-version local content needs explicit backup-and-replace",
        unchanged
        and any("--backup-and-replace" in line for line in blocked)
        and source.read_bytes() == canonical_content
        and (root / f"{installer.BASELINE}.bak").read_bytes() == variation,
        f"blocked={blocked!r}, replaced={replaced!r}",
    )

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = installer.project_source(root)
    source.write_bytes(canonical_content)
    own_agents = root / "AGENTS.md"
    own_agents.write_text("project instructions\n")
    targets = {
        tool: (action,) for tool, action in installer.project_targets(root).items()
    }
    report = installer.install_integrations(source, targets, ["codex"], relative=True)
    original_fetch_available = installer.fetch_available
    installer.fetch_available = lambda: canonical
    with contextlib.redirect_stdout(io.StringIO()):
        partial_result = installer.main(["install", "codex", "--into", str(root)])
    installer.fetch_available = original_fetch_available
    check(
        "existing instruction files are left untouched and reported as incomplete",
        own_agents.read_text() == "project instructions\n"
        and any("left untouched" in line for line in report)
        and partial_result == 1,
        str(report),
    )

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "project"
    outside = Path(tmp) / "outside"
    root.mkdir()
    outside.mkdir()
    source = installer.project_source(root)
    source.write_bytes(canonical_content)
    (root / ".claude").symlink_to(outside, target_is_directory=True)
    targets = {
        tool: (action,) for tool, action in installer.project_targets(root).items()
    }
    report = installer.install_integrations(
        source, targets, ["claude"], relative=True, boundary=root
    )
    check(
        "symlinked parent directories cannot escape the selected scope",
        not (outside / "rules" / installer.BASELINE).exists()
        and any("leaves the selected scope" in line for line in report),
        str(report),
    )

print(f"\nskill installer: {'ok' if not failures else f'{failures} failures'}")
sys.exit(1 if failures else 0)
