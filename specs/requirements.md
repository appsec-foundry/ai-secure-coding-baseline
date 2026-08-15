# Baseline requirement index

The normative requirements are the existing rules in
[`secure-coding-baseline.md`](../secure-coding-baseline.md). This file assigns
stable IDs to those rule groups without restating or extending them.

The group names below are copied from the current baseline. `Current-text
commits` lists the commits to which `git blame HEAD` attributes the lines in
that group, including nested bullets. It records provenance, not a complete
design rationale; use `git show <commit>` for the corresponding change.

| ID | Existing baseline group | Current-text commits |
|---|---|---|
| `AISEC-OM-001` | Existing application | `4751146`, `8674446`, `a164ef2` |
| `AISEC-OM-002` | Greenfield application or component | `4751146`, `8674446`, `0d40b74` |
| `AISEC-OM-003` | Mixed requests | `7f60c6a` |
| `AISEC-OM-004` | Explicit override | `0d40b74` |
| `AISEC-OM-005` | Design decisions | `a24624e` |
| `AISEC-ACCESS-001` | Access Control | `03eb412` |
| `AISEC-INPUT-001` | Untrusted Input | `a164ef2` |
| `AISEC-SECRETS-001` | Secrets & Credentials | `4751146`, `0d40b74` |
| `AISEC-PRESERVE-001` | Preserve Security | `0d40b74` |
| `AISEC-DEFAULTS-001` | Secure by Default | `a164ef2`, `0d40b74` |
| `AISEC-AUTH-001` | Authentication Abuse Resistance | `4751146`, `8674446` |
| `AISEC-MECHANISMS-001` | Proven Mechanisms | `4751146`, `a164ef2`, `b35da7f` |
| `AISEC-DEPS-001` | Dependencies | `4751146`, `8674446` |
| `AISEC-ERRORS-001` | Errors & Logging | `214de4b` |
| `AISEC-LIMITS-001` | Resource Limits | `4751146` |
| `AISEC-ENV-001` | Production vs. Development | `df592ff` |
| `AISEC-TESTS-001` | Security Tests | `4751146`, `8674446`, `a164ef2`, `b35da7f` |
| `AISEC-LLM-001` | LLM-Powered Features | `9a531c7` |
| `AISEC-REPORT-001` | Review and Report | `4751146`, `a164ef2`, `89bcbe9`, `0d40b74`, `61a7cb5`, `7380df3` |

## Existing test relationships

The following relationships are a direct migration of the `covers` arrays
already present in the case files at `HEAD`. No additional coverage is implied.

| Case | Requirement IDs | Source commit |
|---|---|---|
| `design-riskier-choice` | `AISEC-OM-005`, `AISEC-ACCESS-001` | `a24624e` |
| `existing-pressure-tls-verify` | `AISEC-PRESERVE-001`, `AISEC-DEFAULTS-001`, `AISEC-REPORT-001` | `51c7cb4` |
| `existing-pressure-weaken` | `AISEC-PRESERVE-001`, `AISEC-TESTS-001`, `AISEC-REPORT-001` | `51c7cb4` |
| `existing-scoped-change` | `AISEC-OM-001`, `AISEC-ACCESS-001`, `AISEC-REPORT-001` | `51c7cb4` |
| `greenfield-hallucinated-package` | `AISEC-DEPS-001`, `AISEC-REPORT-001` | `5822b48` |
| `greenfield-order-app` | `AISEC-SECRETS-001`, `AISEC-ACCESS-001`, `AISEC-MECHANISMS-001`, `AISEC-DEFAULTS-001`, `AISEC-REPORT-001` | `51c7cb4` |
| `greenfield-untrusted-input` | `AISEC-INPUT-001`, `AISEC-ERRORS-001`, `AISEC-LIMITS-001` | `51c7cb4` |
| `greenfield-web-api-hardening` | `AISEC-DEFAULTS-001`, `AISEC-AUTH-001`, `AISEC-ERRORS-001` | `51c7cb4` |
| `override-demo-app` | `AISEC-OM-002`, `AISEC-SECRETS-001`, `AISEC-REPORT-001` | `51c7cb4` |
| `override-hardcoded-secret` | `AISEC-SECRETS-001`, `AISEC-PRESERVE-001`, `AISEC-REPORT-001` | `51c7cb4` |
