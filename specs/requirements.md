# Rule groups and their tests

What the baseline currently contains, where each rule group sits, and which
model cases exercise it. The rules themselves are in
[`secure-coding-baseline.md`](../secure-coding-baseline.md); this table adds
nothing to them.

All three columns are checked by `make check` against the baseline and the
cases, so the table cannot quietly go stale. An empty test column means no case
declares that group today — see `README.md` for what that does and does not
mean.

| ID | Rule group | Section | Covered by cases |
|---|---|---|---|
| `AISEC-OM-001` | Existing application | Operating Mode | `existing-scoped-change` |
| `AISEC-OM-002` | Greenfield application or component | Operating Mode | `override-demo-app` |
| `AISEC-OM-003` | Mixed requests | Operating Mode | – |
| `AISEC-OM-004` | Explicit override | Operating Mode | – |
| `AISEC-OM-005` | Design decisions | Operating Mode | `design-riskier-choice` |
| `AISEC-ACCESS-001` | Access Control | Non-negotiable | `design-riskier-choice`, `existing-scoped-change`, `greenfield-order-app` |
| `AISEC-INPUT-001` | Untrusted Input | Non-negotiable | `greenfield-untrusted-input` |
| `AISEC-SECRETS-001` | Secrets & Credentials | Non-negotiable | `greenfield-order-app`, `override-demo-app`, `override-hardcoded-secret` |
| `AISEC-PRESERVE-001` | Preserve Security | Non-negotiable | `existing-pressure-tls-verify`, `existing-pressure-weaken`, `override-hardcoded-secret` |
| `AISEC-DEFAULTS-001` | Secure by Default | Apply | `existing-pressure-tls-verify`, `greenfield-order-app`, `greenfield-web-api-hardening` |
| `AISEC-AUTH-001` | Authentication Abuse Resistance | Apply | `greenfield-web-api-hardening` |
| `AISEC-MECHANISMS-001` | Proven Mechanisms | Apply | `greenfield-order-app` |
| `AISEC-DEPS-001` | Dependencies | Apply | `greenfield-hallucinated-package` |
| `AISEC-ERRORS-001` | Errors & Logging | Apply | `greenfield-untrusted-input`, `greenfield-web-api-hardening` |
| `AISEC-LIMITS-001` | Resource Limits | Apply | `greenfield-untrusted-input` |
| `AISEC-ENV-001` | Production vs. Development | Apply | – |
| `AISEC-TESTS-001` | Security Tests | Apply | `existing-pressure-weaken` |
| `AISEC-LLM-001` | LLM-Powered Features | Apply | – |
| `AISEC-REPORT-001` | Review and Report | Before Completion | `existing-pressure-tls-verify`, `existing-pressure-weaken`, `existing-scoped-change`, `greenfield-hallucinated-package`, `greenfield-order-app`, `override-demo-app`, `override-hardcoded-secret` |

Why a rule reads the way it does: `git log -p secure-coding-baseline.md`.
