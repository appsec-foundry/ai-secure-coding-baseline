#!/usr/bin/env python3
"""Check that install.py links where it should and leaves everything else alone.

An installer that quietly overwrites a project's own AGENTS.md destroys work
that is not its own, and one that is not idempotent cannot be run twice. Both
are checked here against a throwaway directory.
"""

import base64
import os
import subprocess
import sys
import tempfile
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install  # noqa: E402

failures = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global failures
    print(f"{'ok  ' if condition else 'FAIL'} {name}")
    if not condition:
        failures += 1
        if detail:
            print(f"     {detail}")


def run(root: Path, *tools: str) -> list[str]:
    return install.install(list(tools) or list(install.TOOLS), root, None)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    report = run(root)

    baseline = root / install.BASELINE
    check("the project gets the real baseline", baseline.is_file())
    check("Claude reads it from .claude/rules",
          (root / ".claude" / "rules" / install.BASELINE).is_symlink())
    check("the AGENTS.md tools read it from the root",
          (root / "AGENTS.md").is_symlink())
    check("Copilot reads it from .github",
          (root / ".github" / "copilot-instructions.md").is_symlink())
    check("links resolve to the project's own file",
          (root / "AGENTS.md").resolve() == baseline.resolve())
    check("links stay relative, so a clone keeps working",
          not Path((root / "AGENTS.md").readlink()).is_absolute(),
          str((root / "AGENTS.md").readlink()))
    check("every step is reported", len(report) >= 4, str(report))

    again = run(root)
    check("a second run changes nothing",
          all(line.startswith("in place") for line in again), str(again))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    own = root / "AGENTS.md"
    own.write_text("# our own instructions\n")
    report = run(root, "codex")

    check("an existing AGENTS.md survives untouched",
          own.read_text() == "# our own instructions\n")
    check("and the manual step is named",
          any("append" in line for line in report), str(report))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    stale = root / "AGENTS.md"
    stale.symlink_to("somewhere-else.md")
    report = run(root, "codex")
    check("a foreign symlink is refused, not replaced",
          stale.readlink() == Path("somewhere-else.md")
          and any("points elsewhere" in line for line in report), str(report))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    occupied = root / install.BASELINE
    occupied.write_text("not a baseline\n")
    report = run(root, "codex")
    check("an unrelated baseline filename survives untouched",
          occupied.read_text() == "not a baseline\n")
    check("invalid baseline content blocks tool links",
          not (root / "AGENTS.md").exists()
          and any("not a valid baseline" in line for line in report), str(report))

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    report = install.install(["claude", "codex"], home, home)
    source = install.user_source(home)
    check("user installs keep a managed baseline outside the checkout",
          source.is_file() and source.resolve() != install.SOURCE.resolve())
    check("Claude's user link reads the managed baseline",
          (home / ".claude" / install.BASELINE).resolve() == source.resolve())
    check("Claude imports the managed baseline",
          f"@{source}" in (home / ".claude" / "CLAUDE.md").read_text().splitlines())
    check("Codex's user instructions read the managed baseline",
          (home / ".codex" / "AGENTS.md").resolve() == source.resolve(), str(report))

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    manual = home / ".codex" / "AGENTS.md"
    manual.parent.mkdir()
    manual.write_bytes(install.bundled_baseline().content)
    found = install.scan_user(home)
    check("known user locations reveal manually copied baselines",
          len(found) == 1
          and found[0].kind == "unmanaged"
          and found[0].tools == ("codex",))

with tempfile.TemporaryDirectory() as tmp:
    state = Path(tmp) / "installations.json"
    state.write_text("not json\n")
    _registry, writable, note = install.load_registry(state)
    check("an invalid installation registry is never overwritten",
          not writable and note is not None and state.read_text() == "not json\n")

check("stable SemVer sorts after its prerelease",
      install.SemVer.parse("1.0.0-rc.1") < install.SemVer.parse("1.0.0"))
check("numeric SemVer prereleases sort numerically",
      install.SemVer.parse("1.0.0-2") < install.SemVer.parse("1.0.0-10"))
try:
    install.SemVer.parse("1.0.0-01")
except ValueError:
    invalid_semver_rejected = True
else:
    invalid_semver_rejected = False
check("invalid SemVer numeric prereleases are rejected", invalid_semver_rejected)

tool_prompts: list[str] = []
tool_output: list[str] = []
chosen_tools = install.choose_tools(
    lambda prompt: tool_prompts.append(prompt) or "1,2",
    tool_output.append,
    ("claude", "codex"),
)
check("guided tool selection clearly supports multiple tools",
      chosen_tools == ["claude", "codex"]
      and any("one or more" in line for line in tool_output)
      and any("comma-separated" in prompt and "Enter = all" in prompt
              for prompt in tool_prompts),
      f"prompts={tool_prompts!r}, output={tool_output!r}")

bundled = install.bundled_baseline()
check("the checkout installer uses the canonical upstream",
      install.GITHUB_REPOSITORY == "appsec-foundry/ai-secure-coding-baseline")
new_content = bundled.content.replace(
    bundled.baseline_id.encode(), b"aisec-9.8.7", 1
)

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    home.mkdir()
    project.mkdir()
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    install.install(["codex"], project, None, content=bundled.content)
    install.install(["codex"], home, home, content=old_content)
    state = sandbox / "installations.json"
    status_output: list[str] = []
    status_result = install.installation_status(
        home=home,
        output=status_output.append,
        check_online=False,
        state_path=state,
        current_root=project,
    )
    check("status check marks current and outdated installations",
          status_result == 0
          and any(line.startswith("  ✓ project baseline:")
                  for line in status_output)
          and any(line.startswith("  ↻ managed user baseline:")
                  for line in status_output),
          str(status_output))
    check("status check is read-only", not state.exists(), str(state))


def fake_release(url: str) -> object:
    if url == install.LATEST_RELEASE_URL:
        return {"tag_name": "v9.8.7", "draft": False, "prerelease": False}
    return {
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(new_content).decode(),
    }


release = install.fetch_release_baseline(fake_release)
check("a tagged release baseline is parsed and version-matched",
      str(release.version) == "9.8.7")


def mismatched_release(url: str) -> object:
    if url == install.LATEST_RELEASE_URL:
        return {"tag_name": "v9.8.6", "draft": False, "prerelease": False}
    return fake_release(url)


try:
    install.fetch_release_baseline(mismatched_release)
except ValueError:
    mismatch_rejected = True
else:
    mismatch_rejected = False
check("a release tag cannot supply a different baseline version", mismatch_rejected)

try:
    install._GitHubRedirectHandler().redirect_request(
        None, None, 302, "redirect", {}, "https://example.com/baseline"
    )
except urllib.error.HTTPError:
    redirect_rejected = True
else:
    redirect_rejected = False
check("the updater rejects cross-host redirects", redirect_rejected)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    install.install(["codex"], root, None, content=old_content)
    first = install.scan_project(root, {})
    tracked = install.Installation(
        first.kind, first.root, first.source, first.baseline, first.tools,
        first.baseline.digest,
    )
    report, updated = install.update_installation(
        tracked, bundled, lambda _question, _default: False
    )
    check("a tracked baseline updates without a second overwrite prompt",
          updated is not None and updated.baseline.digest == bundled.digest, str(report))
    check("a tracked update does not create a backup",
          not (root / f"{install.BASELINE}.bak").exists())

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    install.install(["codex"], root, None, content=old_content)
    first = install.scan_project(root, {})
    changed_content = old_content + b"\nlocal note\n"
    (root / install.BASELINE).write_bytes(changed_content)
    changed = install.scan_project(root, {"sha256": first.baseline.digest})
    report, updated = install.update_installation(
        changed, bundled, lambda _question, _default: False
    )
    check("a locally changed baseline is not replaced by default",
          updated is None and (root / install.BASELINE).read_bytes() == changed_content,
          str(report))
    report, updated = install.update_installation(
        changed, bundled, lambda _question, _default: True
    )
    check("an explicitly approved local replacement keeps a backup",
          updated is not None
          and (root / f"{install.BASELINE}.bak").read_bytes() == changed_content,
          str(report))

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    old_checkout = home / "old-checkout"
    old_checkout.mkdir()
    old_source = old_checkout / install.BASELINE
    old_source.write_bytes(bundled.content)
    target = home / ".codex" / "AGENTS.md"
    target.parent.mkdir()
    target.symlink_to(old_source)
    legacy = install.scan_user(home)
    report, migrated = install.migrate_legacy_user(legacy[0], bundled)
    check("checkout-linked user installs migrate to managed storage",
          migrated is not None
          and target.resolve() == install.user_source(home).resolve(), str(report))
    check("migration does not modify the old checkout",
          old_source.read_bytes() == bundled.content)

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    home.mkdir()
    project.mkdir()
    state = home / "state.json"
    answers = iter(["3", ""])
    output: list[str] = []
    result = install.interactive_setup(
        home=home,
        input_fn=lambda _prompt: next(answers),
        output=output.append,
        check_online=False,
        state_path=state,
        current_root=project,
    )
    check("guided setup can install all supported user tools",
          result == 0
          and install.user_source(home).is_file()
          and (home / ".codex" / "AGENTS.md").is_symlink(), str(output))
    check("user-wide setup explains the Copilot project limitation",
          any("GitHub Copilot" in line and "project" in line for line in output),
          str(output))
    state_mode = os.stat(state).st_mode & 0o777 if state.exists() else None
    check("guided setup records known installation locations",
          state.is_file() and state_mode == 0o600, str(state_mode))

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    home.mkdir()
    project.mkdir()
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    install.install(["codex"], project, None, content=old_content)
    previous = install.scan_project(project, {})
    registry = install.empty_registry()
    install.record_installation(registry, previous, trusted=True)
    state = sandbox / "state.json"
    install.save_registry(state, registry)
    current = sandbox / "current"
    current.mkdir()
    output = []
    prompts: list[str] = []

    def update_answers(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    result = install.interactive_setup(
        home=home,
        input_fn=update_answers,
        output=output.append,
        check_online=False,
        state_path=state,
        current_root=current,
    )
    check("guided setup offers and applies registered project updates",
          result == 0
          and install.read_baseline(project / install.BASELINE).digest == bundled.digest,
          str(output))
    check("an update does not hide the next-action menu",
          any("Update project" in prompt for prompt in prompts)
          and "\nNext action" in output,
          f"prompts={prompts!r}, output={output!r}")

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    home.mkdir()
    project.mkdir()
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    install.install(["codex"], home, home, content=old_content)
    previous = [item for item in install.scan_user(home, {}) if item.kind == "user"][0]
    registry = install.empty_registry()
    install.record_installation(registry, previous, trusted=True)
    state = sandbox / "state.json"
    install.save_registry(state, registry)
    answers = iter(["", "1", "2"])
    prompts = []
    output = []

    def update_user_then_project(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    result = install.interactive_setup(
        home=home,
        input_fn=update_user_then_project,
        output=output.append,
        check_online=False,
        state_path=state,
        current_root=project,
    )
    check("user-only setup clearly offers the current project",
          result == 0
          and "  - no managed project installation" in output
          and any("Install in current project" in line for line in output),
          str(output))
    check("a user update can be followed by a project install",
          install.read_baseline(install.user_source(home)).digest == bundled.digest
          and (project / "AGENTS.md").is_symlink()
          and any("Update user-wide from" in prompt for prompt in prompts),
          f"prompts={prompts!r}, output={output!r}")

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    current = sandbox / "current"
    project = sandbox / "known-project"
    home.mkdir()
    current.mkdir()
    project.mkdir()
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    install.install(["codex"], home, home, content=old_content)
    install.install(["codex"], project, None, content=old_content)
    registry = install.empty_registry()
    user_installation = [
        item for item in install.scan_user(home, {}) if item.kind == "user"
    ][0]
    install.record_installation(registry, user_installation, trusted=True)
    install.record_installation(
        registry, install.scan_project(project, {}), trusted=True
    )
    state = sandbox / "state.json"
    install.save_registry(state, registry)
    answers = iter(["n", "n", "4"])
    prompts = []

    def decline_separate_updates(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    install.interactive_setup(
        home=home,
        input_fn=decline_separate_updates,
        output=lambda _line: None,
        check_online=False,
        state_path=state,
        current_root=current,
    )
    update_prompts = [prompt for prompt in prompts if prompt.startswith("Update ")]
    check("different scopes receive separate update decisions",
          len(update_prompts) == 2
          and any("user-wide" in prompt for prompt in update_prompts)
          and any("known-project" in prompt for prompt in update_prompts),
          str(prompts))

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    current = sandbox / "current"
    target = sandbox / "target"
    home.mkdir()
    current.mkdir()
    target.mkdir()
    old_content = bundled.content.replace(
        bundled.baseline_id.encode(), b"aisec-0.0.1", 1
    )
    (target / install.BASELINE).write_bytes(old_content)
    answers = iter(["2", str(target), "", "y", "2"])
    output = []
    result = install.interactive_setup(
        home=home,
        input_fn=lambda _prompt: next(answers),
        output=output.append,
        check_online=False,
        state_path=sandbox / "state.json",
        current_root=current,
    )
    check("an unlinked project baseline is checked before tools are added",
          result == 0
          and install.read_baseline(target / install.BASELINE).digest == bundled.digest
          and (target / f"{install.BASELINE}.bak").read_bytes() == old_content
          and (target / "AGENTS.md").is_symlink(),
          str(output))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    same_version_content = bundled.content + b"\nlocal variation\n"
    install.install(["codex"], root, None, content=same_version_content)
    found = install.scan_project(root, {})
    check("same-version content differences are not reported as current",
          found is not None and found.has_update(bundled))

setup_script = install.REPO / "setup.sh"
completed = subprocess.run(
    ["bash", str(setup_script), "--help"],
    capture_output=True,
    text=True,
    cwd=tempfile.gettempdir(),
)
check("setup.sh is executable and reaches the installer",
      os.access(setup_script, os.X_OK)
      and completed.returncode == 0
      and "usage: install.py" in completed.stdout,
      completed.stderr or completed.stdout)

print(f"\ninstall: {'ok' if not failures else f'{failures} failures'}")
sys.exit(1 if failures else 0)
