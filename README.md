# AI Secure Coding Baseline

A short set of secure-coding rules for AI coding assistants. Drop it into a project and Claude Code, Copilot, or Codex will follow it when they write or change code.

> **Limitations**
>
> This baseline guides an LLM; it is not an enforceable control or a guarantee of secure code. Supplement it with project-specific instructions and independently validate changes through review, tests, dependency and secret scanning, SAST, and CI or pre-commit checks as appropriate.

The core baseline is deliberately compact: its current 7.9 KB are roughly 2,000 model tokens, while the optional 1.8 KB AI add-on adds roughly 450 more. Exact counts vary by tokenizer, and tools may account for cached input differently. The wording has been repeatedly reviewed, tested in AI-assisted coding tasks, and refined to keep important rules visible with low context overhead; this practical testing is not a formal security certification.

## Why this exists

AI assistants can cut security corners in predictable ways: disable a check to get a test green, import a package that does not exist, log a secret, trust unvalidated input, expose a stack trace, or rewrite unrelated working code. Clear project guidance makes secure choices more consistent.

For existing applications, the baseline stays within the changed code, reuses project controls, and reports relevant pre-existing issues instead of silently fixing them. For greenfield work, it requires applicable controls and tests as part of the design.

## Covered risks

This is a compact guardrail, not a complete standard or compliance checklist. It addresses:

- **Common application risks:** major classes also represented in the [OWASP Top 10:2025](https://owasp.org/Top10/2025/), including access control, misconfiguration, supply-chain and integrity failures, cryptography, injection, insecure design, authentication, logging, and error handling.
- **AI-assisted coding risks:** package hallucinations and slopsquatting through independent, current verification instead of model confidence or package existence alone, plus unsafe scope expansion and weakened controls. See the [OWASP npm Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html#slopsquatting-attacks).
- **Dependency supply chains:** unnecessary or unverified packages, unexpected transitive changes, unreviewed install scripts, missing lockfiles, non-reproducible builds, and absent dependency scanning.
- **LLM application risks:** when the optional add-on is loaded, prompt injection, unsafe model output and tool use, excessive agency, and data or memory exposure, reviewed against the [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) and [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).

## The rules

The full text is in [ai-secure-coding-baseline.md](ai-secure-coding-baseline.md). Its thirteen rules are ordered by risk, with the first four marked non-negotiable:

They cover access control, untrusted input, secrets and default credentials, preserving existing controls, secure defaults and platform protections, authentication abuse resistance, privilege separation, proven mechanisms, dependency supply chains, errors and logging, resource limits, development versus production, and representative negative or abuse tests.

Before completion, the assistant reviews its diff against the baseline and reports concrete security findings—including fixed issues—affected controls, test results, and unresolved risks or verification gaps as applicable.

## Optional AI application add-on

For a project that builds LLM-powered features, also load [ai-secure-coding-ai-add-on.md](ai-secure-coding-ai-add-on.md). It covers AI-specific risks such as prompt injection, tool authorization, action limits, memory isolation, and the OWASP LLM and Agentic Top 10 reviews. Do not load it for ordinary projects that only use an AI assistant to write code.

## Using it

Tools load instructions from fixed locations. Apply the same baseline to one project, your machine or account, or an organization.

### Keep the baseline as a separate file

If a tool can be instructed to read another repository file, add this to its normal project-instructions file:

```markdown
Before making any code changes, read `ai-secure-coding-baseline.md` in this repository and follow all rules defined there.
```

This is an instruction to read the file, not a native import; Claude Code's `@` syntax below is the exception.

### Claude Code

Claude Code can import the baseline directly.

- **Project:** put `ai-secure-coding-baseline.md` in the repo and import it from the project `CLAUDE.md`:

  ```markdown
  # CLAUDE.md
  @ai-secure-coding-baseline.md
  ```

- **Your machine:** do the same import from `~/.claude/CLAUDE.md`, pointing at an absolute path:

  ```markdown
  @/absolute/path/to/ai-secure-coding-baseline.md
  ```

- **Organization:** deploy it as a managed-policy `CLAUDE.md`; managed settings or plugins can add enforceable controls. See the [Claude Code organization setup](https://code.claude.com/docs/en/admin-setup).

### GitHub Copilot

Copilot instruction support varies by surface. Copy the baseline into `.github/copilot-instructions.md` for broad repository coverage.

- **Project:** copy them into `.github/copilot-instructions.md`:

  ```bash
  mkdir -p .github
  cp ai-secure-coding-baseline.md .github/copilot-instructions.md
  ```

- **Your account:** paste it into personal custom instructions for Copilot Chat on GitHub.
- **Organization:** add it as organization custom instructions for supported GitHub.com features. See the [Copilot instruction support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

### OpenAI Codex

Codex reads `AGENTS.md` automatically but cannot import the baseline.

- **Project:** copy the rules into `AGENTS.md` at the repo root:

  ```bash
  cp ai-secure-coding-baseline.md AGENTS.md
  ```

- **Your machine:** put them in `~/.codex/AGENTS.md`.
- **Organization:** distribute a global `AGENTS.md` through endpoint management or include project `AGENTS.md` files in repository templates. Keep enforceable runtime policy separate in managed configuration. See the [Codex `AGENTS.md` guide](https://developers.openai.com/codex/guides/agents-md/) and [admin rollout guide](https://developers.openai.com/codex/enterprise/admin-setup/).

### Keeping the copies in sync

Keep `ai-secure-coding-baseline.md` as the source of truth and generate copied instruction files from it to prevent drift. An organization template can provide those files to new repositories.

## Background

[Scheurer, Balesni, and Hobbhahn (2024)](https://arxiv.org/abs/2311.07590) show that instructions can reduce, but not eliminate, undesirable behavior in a pressured scenario. [Wallace et al. (2024)](https://arxiv.org/abs/2404.13208) describe how instruction-hierarchy training can improve robustness.
