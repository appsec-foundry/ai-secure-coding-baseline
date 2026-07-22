# AI Secure Coding Baseline

**Scope:** These rules apply to the code you write or change. Match the existing codebase's patterns and reuse its mechanisms; do not refactor, rewrite, or "harden" surrounding working code that your change does not touch. Prefer the smallest change that meets the rule over a broad rework.

**Flag, don't fix:** When you encounter a pre-existing security issue in or next to the code you touch, flag it: state the risk in one or two lines and stop. Do not fix it unless asked, and do not let it block the task. Flag only what you actually come across; do not expand into a repo-wide audit.

## Non-negotiable

- **Access Control:** Enforce authn/authz server-side for every protected action and resource; check the authenticated identity against the requested resource; never trust client-side checks or user-supplied identifiers to decide access.
- **Untrusted Input:** Validate every value crossing a trust boundary against expected type, range, and format at the entry point; when passing it onward, use safe APIs or context-correct encoding: parameterized queries, output encoding, safe file/path handling, allow-listed outbound URLs (SSRF).
- **Secrets:** Never put real secrets in code, tests, examples, logs, or committed config; use clearly artificial values in tests and examples; never log credentials, tokens, or PII.
- **Preserve Security:** Never disable or weaken a control to make code work or tests pass; name significant risks, assumptions, and trade-offs a change introduces instead of hiding them.

## Apply

- **Secure by Default:** Least privilege, deny-by-default, smallest attack surface; fail closed when required security context is missing, invalid, or ambiguous.
- **Privilege Separation:** Run privileged operations in a dedicated context under a separate identity with only the permissions that operation needs; do not widen an existing context to reach them.
- **Proven Mechanisms:** Reuse the project's established, sound mechanisms and actively maintained libraries; if one is weak, flag it rather than silently replacing it. Never hand-roll crypto, auth, or session handling. Use vetted algorithms and a CSPRNG: no MD5/SHA-1 for security, no `Math.random` for tokens, and hash passwords with a slow KDF (argon2/bcrypt).
- **Dependencies:** Prefer existing dependencies; add one only when necessary, verify its exact name and intended source (guard against typo/hallucinated packages), and follow the project's dependency workflow.
- **Errors & Logging:** Fail without leaking internals: no stack traces, internal paths, or raw exceptions to clients; log security-relevant events (authn/authz decisions, input rejections) with enough context to investigate, without sensitive data.
- **Resource Limits:** Bound input-driven work: timeouts, size/pagination caps, no unbounded loops or user-supplied regex. Assume any external call can hang or fail.
- **Production vs. Test:** Treat code as production when its context is uncertain; keep test-only mocks and security bypasses out of production execution paths.

## Before Commit

- **Review the Diff:** Before committing, review the changed diff against this baseline; report or resolve concrete findings in the changed code.
