#!/usr/bin/env python3
"""Check that the example gate blocks what it claims to block -- and nothing else.

Three things are tested, because a gate can fail in three independent ways.

Every rule has a sample it must deny and a sample it must allow. The allow half
is the important one: a rule that fires on ordinary code gets the whole gate
removed from someone's settings, after which it protects nothing.

Every rule id must name a rule group that exists in `secure-coding-baseline.md`.
The gate's only claim to authority is the baseline; a finding citing an id that
was renamed or retired is a finding nobody can look up.

The hook contract is exercised end to end, through a real process with a real
payload on stdin, because `decide()` returning the right dict proves nothing
about what Claude Code receives.

What is not tested here: whether an assistant actually follows the baseline.
That needs a model, and it lives in `tests/cases/`.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "gate.py"
BASELINE = HERE.parent.parent / "secure-coding-baseline.md"

sys.path.insert(0, str(HERE))
import gate  # noqa: E402

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_payload(content: str, path: str = "/srv/app/service.py") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": path, "content": content},
    }


def denies(content: str, path: str = "/srv/app/service.py") -> dict | None:
    return gate.decide(write_payload(content, path))


# (rule title fragment, denied sample, allowed sample)
SAMPLES: tuple[tuple[str, str, str], ...] = (
    (
        "TLS certificate verification",
        'resp = requests.get(url, verify=False)',
        'resp = requests.get(url, verify=True, timeout=10)',
    ),
    (
        "TLS certificate verification",
        'const agent = new https.Agent({ rejectUnauthorized: false })',
        'const agent = new https.Agent({ ca: fs.readFileSync(caPath) })',
    ),
    (
        "TLS certificate verification",
        'tls.Config{InsecureSkipVerify: true}',
        'tls.Config{MinVersion: tls.VersionTLS12}',
    ),
    (
        "off switch",
        'SKIP_AUTH = os.environ.get("SKIP_AUTH") == "1"',
        'AUTH_ENABLED = True',
    ),
    (
        "off switch",
        'CSRF_ENABLED = False',
        'if not request.user.is_authenticated:\n    raise PermissionDenied',
    ),
    (
        "unsafe deserializer",
        'config = yaml.load(body)',
        'config = yaml.safe_load(body)',
    ),
    (
        "unsafe deserializer",
        'state = pickle.loads(request.data)',
        'state = json.loads(request.data)',
    ),
    (
        "fast digest",
        'stored = hashlib.sha256(password.encode()).hexdigest()',
        'stored = bcrypt.hashpw(password.encode(), bcrypt.gensalt())',
    ),
    (
        "non-cryptographic random",
        'token = str(random.randint(100000, 999999))',
        'token = secrets.token_urlsafe(32)',
    ),
    (
        "non-cryptographic random",
        'const resetToken = Math.random().toString(36)',
        'const resetToken = crypto.randomBytes(32).toString("hex")',
    ),
    (
        "provider prefix",
        'STRIPE_KEY = "sk-live_51Hxxxxxxxxxxxxxxxxxxxxxxxx"',
        'STRIPE_KEY = os.environ["STRIPE_KEY"]',
    ),
    (
        "provider prefix",
        'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"',
        'aws_access_key_id = settings.require("AWS_ACCESS_KEY_ID")',
    ),
    (
        "default credential",
        'ADMIN_PASSWORD = "changeme"',
        'ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]',
    ),
    (
        "CORS wildcard",
        'app.use(cors({ origin: "*", credentials: true }))',
        'app.use(cors({ origin: ALLOWED_ORIGINS, credentials: true }))',
    ),
    (
        "Debug server",
        'app.run(host="0.0.0.0", debug=True)',
        'app.run(host="127.0.0.1", port=8000)',
    ),
)

for title_fragment, denied, allowed in SAMPLES:
    response = denies(denied)
    if response is None:
        failures.append(f"not denied: {denied!r}")
    else:
        text = response["hookSpecificOutput"]["permissionDecisionReason"]
        check(
            title_fragment.lower() in text.lower(),
            f"denied {denied!r} but the reason never mentions {title_fragment!r}",
        )
    if denies(allowed) is not None:
        failures.append(f"false positive on ordinary code: {allowed!r}")

# The combination rule must stay a combination: a wildcard origin without
# credentials is a documented, ordinary configuration for a public API.
check(
    denies('res.setHeader("Access-Control-Allow-Origin", "*")') is None,
    "a wildcard origin without credentials should not be denied",
)
check(
    denies('res.setHeader("Access-Control-Allow-Origin", "*")\n'
           'res.setHeader("Access-Control-Allow-Credentials", "true")') is not None,
    "a wildcard origin with credentials should be denied",
)

# A secret must not be repeated back into the transcript by the thing that
# reports it. AISEC-SECRETS-001 binds this file as much as the code it guards.
secret = "ghp_" + "a" * 36
response = denies(f'TOKEN = "{secret}"')
check(response is not None, "a GitHub token literal should be denied")
if response:
    text = response["hookSpecificOutput"]["permissionDecisionReason"]
    check(secret not in text, "the deny reason repeats the secret it found")
    check("<redacted>" in text, "the deny reason should mark the match redacted")

# Payload shapes.
check(
    gate.decide({"tool_name": "Edit", "tool_input": {
        "file_path": "/srv/app/x.py", "new_string": "requests.get(u, verify=False)"}}) is not None,
    "Edit payloads are not scanned",
)
check(
    gate.decide({"tool_name": "Edit", "tool_input": {
        "file_path": "/srv/app/x.py",
        "old_string": "requests.get(u, verify=False)",
        "new_string": "requests.get(u, timeout=5)"}}) is None,
    "an edit that removes the pattern is denied because old_string was scanned",
)
check(
    gate.decide({"tool_name": "MultiEdit", "tool_input": {
        "file_path": "/srv/app/x.py",
        "edits": [{"old_string": "a", "new_string": "b"},
                  {"old_string": "c", "new_string": 'pw = "changeme"'}]}}) is not None,
    "MultiEdit payloads are not scanned",
)
check(
    gate.decide({"tool_name": "NotebookEdit", "tool_input": {
        "notebook_path": "/srv/app/x.ipynb",
        "new_source": "state = pickle.loads(blob)"}}) is not None,
    "NotebookEdit payloads are not scanned",
)
check(
    gate.decide({"tool_name": "Bash", "tool_input": {
        "command": "curl -k https://example.com"}}) is None,
    "the gate decides on tools it does not scan",
)
check(gate.decide({}) is None, "an empty payload should be allowed")
check(
    gate.decide({"tool_name": "Write", "tool_input": {"file_path": 5}}) is None,
    "a malformed path should be allowed, not crash",
)
check(
    denies('verify=False', path=str(HERE / "gate.py")) is None,
    "the gate blocks edits to its own pattern list",
)

# Every cited rule id exists in the baseline.
groups = set(re.findall(r"\*\*\[([A-Z][A-Z0-9-]*)\]", BASELINE.read_text(encoding="utf-8")))
check(bool(groups), f"no rule groups found in {BASELINE}")
for rule in gate.RULES:
    check(
        rule.rule_id in groups,
        f"{rule.rule_id} ({rule.title}) is not a rule group in the baseline",
    )

# The hook contract, through a real process.
proc = subprocess.run(
    [sys.executable, str(GATE)],
    input=json.dumps(write_payload('resp = requests.get(u, verify=False)')),
    capture_output=True, text=True, timeout=30,
)
check(proc.returncode == 0, f"the gate exited {proc.returncode} on a denied edit")
try:
    decision = json.loads(proc.stdout)["hookSpecificOutput"]
    check(decision["hookEventName"] == "PreToolUse", "wrong hookEventName on stdout")
    check(decision["permissionDecision"] == "deny", "stdout does not carry a deny")
    check(bool(decision["permissionDecisionReason"]), "the deny carries no reason")
except (json.JSONDecodeError, KeyError, TypeError) as exc:
    failures.append(f"stdout is not a usable hook decision: {exc}: {proc.stdout!r}")

proc = subprocess.run(
    [sys.executable, str(GATE)],
    input=json.dumps(write_payload('resp = requests.get(u, timeout=5)')),
    capture_output=True, text=True, timeout=30,
)
check(proc.returncode == 0, "the gate should exit 0 when it allows")
check(proc.stdout.strip() == "", f"an allowed edit printed a decision: {proc.stdout!r}")

proc = subprocess.run(
    [sys.executable, str(GATE)],
    input="{not json", capture_output=True, text=True, timeout=30,
)
check(proc.returncode == 0, "a malformed payload should not fail the tool call")
check(proc.stdout.strip() == "", "a malformed payload should produce no decision")
check(bool(proc.stderr.strip()), "a malformed payload should be reported on stderr")

if failures:
    print(f"gate: {len(failures)} problem(s)")
    for problem in failures:
        print(f"  - {problem}")
    sys.exit(1)

print(f"gate: ok ({len(gate.RULES)} rules, {len(SAMPLES)} samples)")
