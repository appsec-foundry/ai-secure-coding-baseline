#!/usr/bin/env python3
"""Example PreToolUse gate: deny the edits that no context can justify.

This is an example. It is not part of the baseline, it does not enforce the
baseline, and installing it changes nothing about what an assistant is required
to do. `secure-coding-baseline.md` stays the normative source; this file only
shows what a deterministic backstop under it can and cannot look like.

Why only a deny list
--------------------
A gate that runs on every write has one failure mode that matters: a wrong deny.
The user removes it from their settings and the next hundred real findings never
happen. So the rules below are limited to patterns that have no legitimate use in
an edit a coding assistant just wrote. Everything that needs context to judge --
a bind to 0.0.0.0, SQL built with an f-string, MD5 over something that is not a
password, a new dependency -- is missing on purpose. Those belong in a warn tier
that asks instead of blocking, and that tier is not part of this example.

What a PreToolUse hook cannot see
---------------------------------
It sees one edit and nothing else. Absence is invisible to it: whether the route
that was just added has an authorization check, whether the login endpoint is
rate limited, whether the session id rotates. Those are questions about the
resulting state, so they belong in a check over the diff or in CI, not here. The
core of the baseline -- scope discipline, the override protocol, whether
authorization actually binds identity to resource -- is not pattern-matchable at
all. `tests/cases/` covers that side, with a model and its uncertainty.

Contract
--------
Reads the Claude Code PreToolUse payload on stdin. Prints a deny decision on
stdout when a rule matches, prints nothing when none does, and always exits 0.
A payload it cannot parse is reported on stderr and allowed: refusing every edit
because the harness changed its JSON shape would cost more than it buys, and the
shape is the harness's, not an attacker's.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# The gate's own directory. Editing it means editing the patterns below, which
# would otherwise match themselves and make this file unmaintainable.
SELF_DIR = Path(os.path.realpath(Path(__file__).resolve().parent))

# Tool -> (field naming the file, fields carrying the text being added).
# Only added text is scanned. Code that was already there is not this edit's
# doing, and blaming an edit for its surroundings is how a gate loses its user.
TOOLS = {
    "Write": ("file_path", ("content",)),
    "Edit": ("file_path", ("new_string",)),
    "MultiEdit": ("file_path", ("edits",)),
    "NotebookEdit": ("notebook_path", ("new_source",)),
}


@dataclass(frozen=True)
class Rule:
    """One denied pattern, tied to the baseline rule group it comes from."""

    rule_id: str
    title: str
    pattern: re.Pattern[str]
    guidance: str
    # A second pattern that must also match somewhere in the added text. Used
    # where a single line is harmless and only the combination is not.
    requires: re.Pattern[str] | None = None
    # Keep the match out of the message. A finding must not become the place a
    # credential gets written down (AISEC-SECRETS-001 applies to this file too).
    redact: bool = False


def _c(pattern: str, ignorecase: bool = False) -> re.Pattern[str]:
    flags = re.VERBOSE
    if ignorecase:
        flags |= re.IGNORECASE
    return re.compile(pattern, flags)


RULES: tuple[Rule, ...] = (
    Rule(
        rule_id="AISEC-PRESERVE-001",
        title="TLS certificate verification disabled",
        pattern=_c(
            r"""
              verify \s* = \s* False \b
            | rejectUnauthorized \s* : \s* false
            | InsecureSkipVerify \s* : \s* true
            | NODE_TLS_REJECT_UNAUTHORIZED \s* [=:] \s* ["']? 0
            | ssl \s* \. \s* _create_unverified_context
            | CURLOPT_SSL_VERIFYPEER \s* , \s* (?: 0 | false )
            | \b curl \b [^\n]* \s (?: -k | --insecure ) \b
            """
        ),
        guidance=(
            "Fix the trust chain instead: install the CA certificate, correct the "
            "hostname, or point the client at the right bundle. Turning the check "
            "off to make the call succeed is the weakening AISEC-PRESERVE-001 "
            "forbids, including temporarily."
        ),
    ),
    Rule(
        rule_id="AISEC-PRESERVE-001",
        title="Authentication, authorization, or CSRF behind an off switch",
        pattern=_c(
            r"""
              \b (?: DISABLE | SKIP | BYPASS | NO ) _
                (?: AUTH | AUTHZ | AUTHENTICATION | AUTHORIZATION
                  | CSRF | XSRF | SECURITY | LOGIN | PERMISSION S? )
            | \b (?: AUTH | AUTHENTICATION | AUTHORIZATION | CSRF | XSRF | SECURITY )
                _ (?: ENABLED | REQUIRED | CHECK S? ) \s* [=:] \s* ["']? (?: false | 0 ) \b
            """,
            ignorecase=True,
        ),
        guidance=(
            "A control that can be switched off is a weakened control, whatever the "
            "flag is called and however clearly it is labelled temporary "
            "(AISEC-PRESERVE-001, AISEC-ENV-001). Make the protected path work with "
            "the control in place, or take the weakening through an explicit "
            "override with the user."
        ),
    ),
    Rule(
        rule_id="AISEC-INPUT-001",
        title="Untrusted data reaching an unsafe deserializer",
        pattern=_c(
            r"""
              yaml \s* \. \s* load \s* \( (?! [^)\n]* Loader \s* = )
            | pickle \s* \. \s* loads \s* \(
            | cPickle \s* \. \s* loads \s* \(
            | jsonpickle \s* \. \s* decode \s* \(
            | new \s+ ObjectInputStream \s* \(
            """
        ),
        guidance=(
            "Use a format that cannot execute on load: yaml.safe_load, JSON, or an "
            "explicit schema. AISEC-INPUT-001 rules out unsafe deserializers on data "
            "crossing a trust boundary, and a deserializer cannot tell you which "
            "side of the boundary its input came from."
        ),
    ),
    Rule(
        rule_id="AISEC-MECHANISMS-001",
        title="Password hashed with a fast digest",
        pattern=_c(
            r"""
              (?: hashlib \s* \. \s* )?
              (?: md5 | sha1 | sha224 | sha256 | sha384 | sha512 ) \s* \(
              [^)\n]* (?: password | passwd | passphrase | \b pwd \b )
            | createHash \s* \( \s* ["'] (?: md5 | sha1 | sha256 | sha512 ) ["'] \s* \)
              [^\n]* (?: password | passwd | \b pwd \b )
            | (?: password | passwd | passphrase ) [^\n]{0,30}
              (?: hashlib \s* \. \s* )? (?: md5 | sha1 | sha256 | sha512 ) \s* \(
            """,
            ignorecase=True,
        ),
        guidance=(
            "Use Argon2, scrypt, bcrypt, or PBKDF2 with sound parameters "
            "(AISEC-MECHANISMS-001). A general-purpose digest is built to be fast, "
            "which is the one property a password hash must not have."
        ),
    ),
    Rule(
        rule_id="AISEC-MECHANISMS-001",
        title="Security value from a non-cryptographic random source",
        pattern=_c(
            r"""
              (?: token | secret | \b key \b | nonce | \b salt \b | \b otp \b
                | password | session _? id | reset _? code | api _? key )
              [^\n]{0,60}
              (?: Math \s* \. \s* random \s* \(
                | random \s* \. \s* (?: random | randint | choice | randrange | uniform ) \s* \( )
            | (?: Math \s* \. \s* random \s* \(
                | random \s* \. \s* (?: random | randint | choice | randrange ) \s* \( )
              [^\n]{0,60}
              (?: token | secret | \b key \b | nonce | \b salt \b | \b otp \b
                | password | session _? id | reset _? code )
            """,
            ignorecase=True,
        ),
        guidance=(
            "Use a CSPRNG: secrets.token_urlsafe, crypto.randomBytes, "
            "java.security.SecureRandom (AISEC-MECHANISMS-001). Math.random and the "
            "random module are predictable from observed output, so a token drawn "
            "from them is guessable."
        ),
    ),
    Rule(
        rule_id="AISEC-SECRETS-001",
        title="Credential literal with a recognisable provider prefix",
        pattern=_c(
            r"""
              ghp_ [A-Za-z0-9]{36}
            | github_pat_ [A-Za-z0-9_]{40,}
            | \b sk- [A-Za-z0-9_-]{20,}
            | \b AKIA [0-9A-Z]{16} \b
            | \b xox [baprs] - [A-Za-z0-9-]{10,}
            | \b AIza [0-9A-Za-z_-]{35} \b
            | -----BEGIN \s (?: [A-Z]+ \s )? PRIVATE \s KEY-----
            """
        ),
        guidance=(
            "AISEC-SECRETS-001: real secrets never go into source. Read it from the "
            "environment or a secret manager and fail startup when it is missing. If "
            "this key exists, treat it as disclosed and rotate it."
        ),
        redact=True,
    ),
    Rule(
        rule_id="AISEC-SECRETS-001",
        title="Well-known default credential",
        pattern=_c(
            r"""
              (?: password | passwd | \b pwd \b | \b pw \b | passphrase | secret
                | api _? key | token | credential s? )
              \s* [=:] \s* ["']
              (?: admin | admin123 | administrator | changeme | change_me | default
                | letmein | password | password1 | password123 | pass123 | root
                | secret | test123 | 123456 | 12345678 | qwerty | welcome )
              ["']
            """,
            ignorecase=True,
        ),
        guidance=(
            "AISEC-SECRETS-001 forbids shipping, seeding, or documenting a working "
            "default credential, and a placeholder the reader is advised to change "
            "is still a shipped default. Require the value from external "
            "configuration and fail startup without it, or generate it with a CSPRNG "
            "at first start and disclose it once to the operator."
        ),
    ),
    Rule(
        rule_id="AISEC-DEFAULTS-001",
        title="CORS wildcard combined with credentials",
        pattern=_c(
            r"""
              Access-Control-Allow-Origin ["']? \s* [,:=] \s* ["'] \* ["']
            | \b origin \s* : \s* ["'] \* ["']
            | setHeader \s* \( \s* ["'] Access-Control-Allow-Origin ["'] \s* , \s* ["'] \* ["']
            """,
            ignorecase=True,
        ),
        requires=_c(
            r"""
              Access-Control-Allow-Credentials ["']? \s* [,:=] \s* ["']? true
            | \b credentials \s* : \s* true
            | withCredentials \s* : \s* true
            """,
            ignorecase=True,
        ),
        guidance=(
            "A wildcard origin with credentials lets any site read authenticated "
            "responses. AISEC-DEFAULTS-001: match an explicit allow-list exactly and "
            "echo only an origin that matched it."
        ),
    ),
    Rule(
        rule_id="AISEC-ENV-001",
        title="Debug server or debug mode enabled in code",
        pattern=_c(
            r"""
              \. run \s* \( [^)\n]* debug \s* = \s* True
            | FLASK_DEBUG \s* [=:] \s* ["']? 1
            | app \s* \. \s* config \s* \[ ["'] DEBUG ["'] \s* \] \s* = \s* True
            | \b DEBUG \s* = \s* True \b [^\n]* \# \s* prod
            """
        ),
        guidance=(
            "The development server and its debugger belong nowhere near production "
            "(AISEC-ENV-001). Run a production server and keep the debug switch in "
            "local configuration that is not the default."
        ),
    ),
)


@dataclass(frozen=True)
class Finding:
    rule: Rule
    line: int
    excerpt: str


def added_text(tool_name: str, tool_input: dict) -> tuple[str, str] | None:
    """The file being written and the text this edit adds, or None if not a write."""
    entry = TOOLS.get(tool_name)
    if not entry:
        return None
    path_field, text_fields = entry
    path = tool_input.get(path_field)
    if not isinstance(path, str) or not path:
        return None

    parts: list[str] = []
    for field in text_fields:
        value = tool_input.get(field)
        if isinstance(value, str):
            parts.append(value)
        elif field == "edits" and isinstance(value, list):
            parts.extend(
                edit["new_string"]
                for edit in value
                if isinstance(edit, dict) and isinstance(edit.get("new_string"), str)
            )
    return (path, "\n".join(parts)) if parts else None


def scans(path: str) -> bool:
    """False for this example's own files, whose patterns would match themselves."""
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
        if rule.requires and not rule.requires.search(text):
            continue
        line = text.count("\n", 0, match.start()) + 1
        excerpt = "<redacted>" if rule.redact else text[match.start():match.end()].strip()
        findings.append(Finding(rule, line, excerpt[:120]))
    return findings


def reason(path: str, findings: list[Finding]) -> str:
    lines = [
        f"Blocked by the example secure-coding gate: {path} adds "
        f"{'a pattern' if len(findings) == 1 else 'patterns'} the baseline rules out."
    ]
    for finding in findings:
        lines.append("")
        lines.append(f"[{finding.rule.rule_id}] {finding.rule.title}")
        lines.append(f"  line {finding.line}: {finding.excerpt}")
        lines.append(f"  {finding.rule.guidance}")
    lines.append("")
    lines.append(
        "Change the approach rather than the pattern. If you believe the rule does "
        "not apply here, say so and let the user decide -- do not restate the same "
        "construct in a form that slips past the match."
    )
    return "\n".join(lines)


def decide(payload: dict) -> dict | None:
    """The hook response that blocks this call, or None to stay out of the way."""
    if payload.get("hook_event_name") not in (None, "PreToolUse"):
        return None
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return None
    target = added_text(tool_name, tool_input)
    if not target:
        return None
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
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        print(f"secure-coding gate: unreadable hook payload ({exc}); allowing",
              file=sys.stderr)
        return 0
    if not isinstance(payload, dict):
        print("secure-coding gate: hook payload is not an object; allowing",
              file=sys.stderr)
        return 0
    response = decide(payload)
    if response:
        print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
