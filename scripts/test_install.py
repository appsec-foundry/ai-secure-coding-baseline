#!/usr/bin/env python3
"""Check that install.py links where it should and leaves everything else alone.

An installer that quietly overwrites a project's own AGENTS.md destroys work
that is not its own, and one that is not idempotent cannot be run twice. Both
are checked here against a throwaway directory.
"""

import base64
import hashlib
import json
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
    report = install.install(list(install.TOOLS), home, home)
    source = install.user_source(home)
    check("user installs keep a managed baseline outside the checkout",
          source.is_file() and source.resolve() != install.SOURCE.resolve())
    check("Claude's user link reads the managed baseline",
          (home / ".claude" / install.BASELINE).resolve() == source.resolve())
    check("Claude imports the managed baseline",
          f"@{source}" in (home / ".claude" / "CLAUDE.md").read_text().splitlines())
    check("Codex's user instructions read the managed baseline",
          (home / ".codex" / "AGENTS.md").resolve() == source.resolve(), str(report))
    check("Copilot's user instructions read the managed baseline",
          (home / ".copilot" / "copilot-instructions.md").resolve()
          == source.resolve(), str(report))

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
all_tools = install.choose_tools(lambda _prompt: "", lambda _line: None, install.TOOLS)
check("guided setup defaults to all three tools", all_tools == list(install.TOOLS))
existing_tool_prompts: list[str] = []
existing_tool_output: list[str] = []
existing_tools = install.choose_tools(
    lambda prompt: existing_tool_prompts.append(prompt) or "",
    existing_tool_output.append,
    install.TOOLS,
    ["codex"],
)
check("existing scopes default to their installed tools",
      existing_tools == ["codex"]
      and "  2. Codex (installed)" in existing_tool_output
      and not any("Claude Code (installed)" in line
                  or "GitHub Copilot (installed)" in line
                  for line in existing_tool_output)
      and any("Enter = keep installed (Codex)" in prompt
              for prompt in existing_tool_prompts),
      f"prompts={existing_tool_prompts!r}, output={existing_tool_output!r}")
hook_output: list[str] = []
hook_prompts: list[str] = []
hook_tools = install.choose_hook_tools(
    lambda prompt: hook_prompts.append(prompt) or "1,3",
    hook_output.append,
    list(install.TOOLS),
)
check("startup hooks can target a subset of the installed tools",
      hook_tools == ["claude", "copilot"]
      and any("Enter = all shown" in prompt for prompt in hook_prompts),
      f"prompts={hook_prompts!r}, output={hook_output!r}")
default_hook_tools = install.choose_hook_tools(
    lambda _prompt: "", lambda _line: None, list(install.TOOLS)
)
check("startup hooks default to all selected tools",
      default_hook_tools == list(install.TOOLS))
no_hook_tools = install.choose_hook_tools(
    lambda _prompt: "none", lambda _line: None, list(install.TOOLS)
)
check("startup hooks can be skipped explicitly", no_hook_tools == [])

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    install.install(list(install.TOOLS), root, None)
    claude_settings = root / ".claude" / "settings.json"
    claude_settings.write_text(
        '{"permissions":{"ask":["Edit(/specs/**)"]}}\n', encoding="utf-8"
    )
    hook_report = install.install_version_hooks(list(install.TOOLS), root, None)
    helper = install.version_hook_path(root, None)
    claude_config = json.loads(claude_settings.read_text(encoding="utf-8"))
    codex_config = json.loads(
        (root / ".codex" / "hooks.json").read_text(encoding="utf-8")
    )
    copilot_config = json.loads(
        (root / ".github" / "hooks" / install.COPILOT_VERSION_HOOK_NAME).read_text(
            encoding="utf-8"
        )
    )
    check("version hooks are installed for all three project tools",
          helper.is_file()
          and "SessionStart" in claude_config["hooks"]
          and "SessionStart" in codex_config["hooks"]
          and "sessionStart" in copilot_config["hooks"], str(hook_report))
    check("the Claude hook merge preserves existing settings",
          claude_config.get("permissions")
          == {"ask": ["Edit(/specs/**)"]}, str(claude_config))
    json_banner = subprocess.run(
        [sys.executable, str(helper), "--output", "json"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    plain_banner = subprocess.run(
        [sys.executable, str(helper), "--output", "message"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    check("the shared hook helper reports the installed baseline ID",
          json_banner.returncode == 0
          and "Baseline active:" in json.loads(json_banner.stdout)["systemMessage"]
          and json.loads(json_banner.stdout)["systemMessage"].endswith(
              install.bundled_baseline().baseline_id
          )
          and plain_banner.stdout.strip().endswith(
              install.bundled_baseline().baseline_id
          ), json_banner.stderr or plain_banner.stderr)
    again = install.install_version_hooks(list(install.TOOLS), root, None)
    check("installing the version hooks twice is idempotent",
          all(line.startswith("in place") for line in again), str(again))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    install.install(["claude"], root, None)
    settings = root / ".claude" / "settings.json"
    invalid = b'{"hooks": {"SessionStart": []}, "hooks": {}}\n'
    settings.write_bytes(invalid)
    report = install.install_version_hooks(["claude"], root, None)
    check("ambiguous existing hook settings are not overwritten",
          settings.read_bytes() == invalid
          and any(line.startswith("blocked") for line in report), str(report))

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
          and any(line.startswith("  ✓") and " project " in line
                  for line in status_output)
          and any(line.startswith("  ↻") and " user " in line
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
    home = Path(tmp)
    old_checkout = home / "old-checkout"
    old_checkout.mkdir()
    old_source = old_checkout / install.BASELINE
    old_source.write_bytes(bundled.content)
    claude_link = home / ".claude" / install.BASELINE
    claude_link.parent.mkdir()
    claude_link.symlink_to(old_source)
    claude_instructions = home / ".claude" / "CLAUDE.md"
    claude_instructions.write_text(f"@{claude_link}\n", encoding="utf-8")
    matches = [
        item for item in install.scan_user(home) if item.kind == "legacy-user"
    ]
    report, migrated = install.migrate_legacy_user(matches[0], bundled)
    install_report = install.install(["claude"], home, home)
    hook_report = install.install_version_hooks(["claude"], home, home)
    managed = [item for item in install.scan_user(home) if item.kind == "user"]
    check("Claude legacy links migrate to managed user storage",
          migrated is not None
          and migrated.tools == ("claude",)
          and claude_link.resolve() == install.user_source(home).resolve()
          and claude_instructions.read_text(encoding="utf-8")
              == f"@{claude_link}\n"
          and managed and managed[0].tools == ("claude",),
          f"migration={report!r}, install={install_report!r}, hook={hook_report!r}")
    check("Claude's stable import link is accepted after migration",
          not any(line.startswith("blocked") for line in install_report),
          str(install_report))
    check("Claude's startup hook works after legacy migration",
          install._version_hook_is_installed("claude", home, home),
          str(hook_report))

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    home.mkdir()
    project.mkdir()
    state = home / "state.json"
    answers = iter(["1", "", ""])
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
          and (home / ".codex" / "AGENTS.md").is_symlink()
          and (home / ".copilot" / "copilot-instructions.md").is_symlink(),
          str(output))
    check("guided setup can add user-wide startup hooks for all three tools",
          (home / ".claude" / "settings.json").is_file()
          and (home / ".codex" / "hooks.json").is_file()
          and (home / ".copilot" / "hooks"
               / install.COPILOT_VERSION_HOOK_NAME).is_file(), str(output))
    check("guided setup explains its purpose and progress",
          output[:4] == [
              "AI Secure Coding Baseline setup",
              "Install or update the baseline for Claude Code, Codex, and Copilot.",
              "Existing instruction files are preserved; conflicts are reported.",
              "\nChecking the available baseline...",
          ]
          and "\nInstallations" in output
          and "\nApplying user-wide setup:" in output
          and "\nVerifying baseline setup:" in output
          and "\nVerifying startup hooks:" in output
          and output[-1] == "\nSetup complete.", str(output))
    state_mode = os.stat(state).st_mode & 0o777 if state.exists() else None
    check("guided setup records known installation locations",
          state.is_file() and state_mode == 0o600, str(state_mode))

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    plain = sandbox / "plain-directory"
    home.mkdir()
    plain.mkdir()
    previous_cwd = Path.cwd()
    output = []
    try:
        os.chdir(plain)
        result = install.interactive_setup(
            home=home,
            input_fn=lambda _prompt: "2",
            output=output.append,
            check_online=False,
            state_path=sandbox / "state.json",
        )
    finally:
        os.chdir(previous_cwd)
    check("project setup is hidden outside a detected project",
          result == 0
          and "Project    none detected" in output
          and "  1. install for user" in output
          and "  2. exit" in output
          and not any("in project" in line for line in output),
          str(output))

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    foreign = sandbox / "foreign"
    home.mkdir()
    project.mkdir()
    foreign.mkdir()
    install.install(["codex"], home, home)
    foreign_source = foreign / install.BASELINE
    foreign_source.write_bytes(bundled.content)
    claude_link = home / ".claude" / install.BASELINE
    claude_link.parent.mkdir()
    claude_link.symlink_to(foreign_source)
    (home / ".claude" / "CLAUDE.md").write_text(
        "Existing Claude instructions.\n", encoding="utf-8"
    )
    answers = iter(["1", "1"])
    output = []
    result = install.interactive_setup(
        home=home,
        input_fn=lambda _prompt: next(answers),
        output=output.append,
        check_online=False,
        state_path=sandbox / "state.json",
        current_root=project,
    )
    check("guided setup reports incomplete tool installation as an error",
          result == 2
          and "  ! Claude Code incomplete" in output
          and output[-1] == "\nSetup finished with unresolved items."
          and not (home / ".claude" / "settings.json").exists(),
          str(output))

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
    prompts: list[str] = []
    result = install.interactive_setup(
        home=home,
        input_fn=lambda prompt: prompts.append(prompt) or "",
        output=lambda _line: None,
        check_online=False,
        state_path=state,
        current_root=project,
    )
    check("a user update defaults to the existing user scope and tools",
          result == 0
          and any(prompt == "Choice [1]: " for prompt in prompts)
          and any("keep installed (Codex)" in prompt for prompt in prompts)
          and (home / ".codex" / "AGENTS.md").is_symlink()
          and not (home / ".claude" / "rules").exists()
          and not (home / ".copilot" / "copilot-instructions.md").exists(),
          str(prompts))

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    home = sandbox / "home"
    project = sandbox / "project"
    checkout = sandbox / "checkout"
    home.mkdir()
    project.mkdir()
    checkout.mkdir()
    source = checkout / install.BASELINE
    source.write_bytes(bundled.content)
    claude_link = home / ".claude" / install.BASELINE
    claude_link.parent.mkdir()
    claude_link.symlink_to(source)
    (home / ".claude" / "CLAUDE.md").write_text(
        f"@{claude_link}\n", encoding="utf-8"
    )
    prompts = []
    answers = iter(["1", "n", "1"])

    def decline_migration(prompt: str) -> str:
        prompts.append(prompt)
        return next(answers)

    result = install.interactive_setup(
        home=home,
        input_fn=decline_migration,
        output=lambda _line: None,
        check_online=False,
        state_path=sandbox / "state.json",
        current_root=project,
    )
    check("the migration prompt explains the change and its benefit",
          result == 2
          and any(
              "Claude Code currently loads the baseline from a repository checkout."
              in prompt
              and "keeps working if that checkout is moved or removed" in prompt
              for prompt in prompts
          ), str(prompts))

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
    check("guided setup ignores projects outside the current scope",
          result == 0
          and install.read_baseline(project / install.BASELINE).digest
              != bundled.digest
          and not any("Update project" in prompt for prompt in prompts)
          and "\nWhat would you like to do?" in output
          and "  1. install for user" in output
          and any(line.startswith("  2. install in project ") for line in output),
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
    answers = iter(["", "2", "2", "n"])
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
    check("the user-first menu clearly offers the current project",
          result == 0
          and any(line.startswith("  -") and "project" in line
                  and "not installed" in line for line in output)
          and "  1. tools for user" in output
          and any(line.startswith("  2. install in project ")
                  and str(project) in line for line in output),
          str(output))
    check("a user update can be followed by a project install",
          install.read_baseline(install.user_source(home)).digest == bundled.digest
          and (project / "AGENTS.md").is_symlink()
          and any("Update user-wide" in prompt for prompt in prompts),
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
    answers = iter(["n", "3"])
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
    update_prompts = [
        prompt for prompt in prompts if prompt.lstrip().startswith("Update ")
    ]
    check("only the active scopes receive update decisions",
          len(update_prompts) == 1
          and "user-wide" in update_prompts[0]
          and install.read_baseline(project / install.BASELINE).digest
              != bundled.digest,
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
    answers = iter(["", "y", "2", "2", "n"])
    output = []
    result = install.interactive_setup(
        home=home,
        input_fn=lambda _prompt: next(answers),
        output=output.append,
        check_online=False,
        state_path=sandbox / "state.json",
        current_root=target,
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
setup_digest = hashlib.sha256(setup_script.read_bytes()).hexdigest()
readme = (install.REPO / "README.md").read_text(encoding="utf-8")
quick_start = readme.split("## Quick start", 1)[1].split("\n## ", 1)[0]
normalized_quick_start = " ".join(quick_start.split())
check("the quick start pins the exact remote bootstrap content",
      f"echo '{setup_digest} aisec-setup.sh' | sha256sum --check"
      in normalized_quick_start)
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

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    remote_setup = sandbox / "remote-setup.sh"
    remote_setup.write_bytes(setup_script.read_bytes())
    remote_setup.chmod(0o755)
    mock_bin = sandbox / "bin"
    mock_bin.mkdir()
    mock_curl = mock_bin / "curl"
    mock_curl.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "output=\n"
        "url=\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --output) output=$2; shift 2 ;;\n"
        "    --proto|--max-time) shift 2 ;;\n"
        "    --fail|--silent|--show-error) shift ;;\n"
        "    *) url=$1; shift ;;\n"
        "  esac\n"
        "done\n"
        "case \"$url\" in\n"
        "  */branches/main)\n"
        "    printf '{\"commit\":{\"sha\":\"%s\"}}\\n' \"$AISEC_TEST_REF\" ;;\n"
        "  */\"$AISEC_TEST_REF\"/*)\n"
        "    path=${url#*\"$AISEC_TEST_REF\"/}\n"
        "    cp \"$AISEC_TEST_REPO/$path\" \"$output\" ;;\n"
        "  *)\n"
        "    echo \"unexpected URL: $url\" >&2; exit 1 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    mock_curl.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = f"{mock_bin}{os.pathsep}{environment['PATH']}"
    environment["AISEC_TEST_REF"] = "a" * 40
    environment["AISEC_TEST_REPO"] = str(install.REPO)
    remote = subprocess.run(
        ["sh", str(remote_setup), "--help"],
        capture_output=True,
        text=True,
        cwd=sandbox,
        env=environment,
    )
    check("setup.sh bootstraps a commit-pinned installer without a checkout",
          remote.returncode == 0 and "usage: install.py" in remote.stdout,
          remote.stderr or remote.stdout)

print(f"\ninstall: {'ok' if not failures else f'{failures} failures'}")
sys.exit(1 if failures else 0)
