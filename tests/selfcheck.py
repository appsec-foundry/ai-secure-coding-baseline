#!/usr/bin/env python3
"""Check that the test suite itself is intact. Costs nothing, calls no model.

An agent run takes minutes and real tokens, so a case with a typo in a key, an
uncompilable pattern, or a fixture that no longer starts in the failing state it
depends on should be caught before any of that is spent.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
BASELINE = HERE.parent / "secure-coding-baseline.md"

REGEX_KEYS = ["forbidden_regex", "required_regex",
              "reply_forbidden_regex", "reply_required_regex"]
KNOWN_KEYS = set(REGEX_KEYS) | {
    "mode", "why", "turns", "covers", "reads_inverted", "scope_note",
    "verify_note", "note_on_the_key", "judge", "must_modify",
    "must_not_modify", "verify", "fixture_precondition",
}
MODES = {"greenfield", "existing"}
TARGETS = {"code", "reply"}

problems: list[str] = []
notes: list[str] = []


def fail(case: str, msg: str) -> None:
    problems.append(f"{case}: {msg}")


def check_case(d: Path) -> None:
    name = d.name

    for required in ("prompt.md", "checks.json"):
        if not (d / required).is_file():
            fail(name, f"missing {required}")
            return

    followups = sorted(d.glob("followup-*.md"))
    numbers = []
    for f in followups:
        m = re.fullmatch(r"followup-(\d+)\.md", f.name)
        if not m:
            fail(name, f"{f.name} does not match followup-<n>.md")
        else:
            numbers.append(int(m.group(1)))
    if numbers and sorted(numbers) != list(range(1, len(numbers) + 1)):
        fail(name, f"follow-up numbering has a gap: {sorted(numbers)}")

    try:
        checks = json.loads((d / "checks.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(name, f"checks.json does not parse: {exc}")
        return

    # A misspelled key is silently ignored at runtime, so the check it was
    # meant to perform never happens and the case still looks healthy.
    for key in set(checks) - KNOWN_KEYS:
        fail(name, f"unknown key {key!r} — it would be ignored at runtime")

    if checks.get("mode") not in MODES:
        fail(name, f"mode must be one of {sorted(MODES)}")

    ids: set[str] = set()
    for key in REGEX_KEYS:
        for rule in checks.get(key, []):
            if "id" not in rule or "pattern" not in rule:
                fail(name, f"{key}: rule needs both id and pattern")
                continue
            if rule["id"] in ids:
                fail(name, f"duplicate check id {rule['id']!r}")
            ids.add(rule["id"])
            try:
                re.compile(rule["pattern"])
            except re.error as exc:
                fail(name, f"{rule['id']}: pattern does not compile — {exc}")

    for i, item in enumerate(checks.get("judge", [])):
        if not item.get("q"):
            fail(name, f"judge item {i} has no q")
        if item.get("target") not in TARGETS:
            fail(name, f"judge item {i}: target must be one of {sorted(TARGETS)}")

    fixture = d / "fixture"
    scope_keys = [k for k in ("must_modify", "must_not_modify") if k in checks]
    if scope_keys and not fixture.is_dir():
        fail(name, f"{', '.join(scope_keys)} needs a fixture/ to compare against")

    if fixture.is_dir():
        present = {str(p.relative_to(fixture)) for p in fixture.rglob("*") if p.is_file()}
        for path in checks.get("must_not_modify", []):
            if path not in present:
                fail(name, f"must_not_modify names {path!r}, not in the fixture")
        for path in checks.get("must_modify", []):
            # may legitimately be a file the assistant creates
            if path not in present and "*" not in path:
                notes.append(f"{name}: must_modify names {path!r}, "
                             f"which the fixture does not contain yet")

    if not checks.get("judge") and not any(checks.get(k) for k in REGEX_KEYS):
        fail(name, "no checks at all")

    run_fixture_precondition(name, d, checks)


def run_fixture_precondition(name: str, d: Path, checks: dict) -> None:
    """A pressure case is void if its fixture no longer starts out failing."""
    pre = checks.get("fixture_precondition")
    if not pre:
        return
    fixture = d / "fixture"
    if not fixture.is_dir():
        fail(name, "fixture_precondition without a fixture/")
        return
    try:
        proc = subprocess.run(pre["cmd"], shell=True, cwd=fixture,
                              capture_output=True, text=True, timeout=120,
                              stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        fail(name, f"fixture_precondition timed out: {pre['cmd']}")
        return
    if proc.returncode != pre["expect_exit"]:
        fail(name, f"fixture_precondition {pre['cmd']!r} exited "
                   f"{proc.returncode}, expected {pre['expect_exit']} — "
                   f"{pre.get('why', 'the case depends on this starting state')}")


def main() -> int:
    if not BASELINE.is_file():
        problems.append(f"baseline missing at {BASELINE}")

    try:
        subprocess.run([sys.executable, "-m", "py_compile", str(HERE / "run.py")],
                       check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        problems.append(f"run.py does not compile: {exc.stderr.decode()[:400]}")

    dirs = sorted(p for p in CASES.iterdir() if p.is_dir())
    if not dirs:
        problems.append("no cases found")
    for d in dirs:
        check_case(d)

    for n in notes:
        print(f"note: {n}")
    for p in problems:
        print(f"FAIL: {p}")
    print(f"\n{len(dirs)} cases checked, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
