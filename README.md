# AI Secure Coding Baseline

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-D97757?logo=anthropic&logoColor=white)](https://code.claude.com/)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-compatible-000000?logo=githubcopilot&logoColor=white)](https://github.com/features/copilot)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-compatible-412991?logo=openai&logoColor=white)](https://developers.openai.com/codex/)

A short set of secure-coding rules for AI coding assistants. Add it to a project's instructions and Claude Code, Copilot, or Codex will follow it when they write or change code.

> **Limitations**
>
> This baseline guides an LLM; it is not an enforceable control or a guarantee of secure code. Supplement it with project-specific instructions and independently validate changes through review, tests, dependency and secret scanning, SAST, and CI or pre-commit checks as appropriate.

The baseline is deliberately compact: ~8.4 KB (roughly 2,100 model tokens), including one condensed rule for LLM-powered features. Counts vary by tokenizer. The wording has been reviewed and refined through AI-assisted coding tasks—practical testing, not a formal security certification.

## Why this exists

AI assistants can cut security corners in predictable ways: disable a check to get a test green, import a package that does not exist, log a secret, trust unvalidated input, expose a stack trace, or rewrite unrelated working code. Clear project guidance makes secure choices more consistent.

For existing applications, the baseline stays within the changed code, reuses project controls, and reports relevant pre-existing issues instead of silently fixing them. For greenfield work, it requires applicable controls and tests as part of the design.

## Covered risks

This is a compact guardrail, not a complete standard or compliance checklist. It addresses:

- **Common application risks:** major classes also represented in the [OWASP Top 10:2025](https://owasp.org/Top10/2025/), including access control, misconfiguration, supply-chain and integrity failures, cryptography, injection, insecure design, authentication, logging, and error handling.
- **AI-assisted coding risks:** package hallucinations and slopsquatting through independent, current verification instead of model confidence or package existence alone, plus unsafe scope expansion and weakened controls. See the [OWASP npm Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html#slopsquatting-attacks).
- **Dependency supply chains:** unnecessary or unverified packages, unexpected transitive changes, unreviewed install scripts, missing lockfiles, non-reproducible builds, and absent dependency scanning.
- **LLM application risks:** prompt injection, unsafe model output and tool use, excessive agency, and data or memory exposure—covered by one condensed rule in the baseline—reviewed against the [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) and [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).

## The rules

The full text is in [secure-coding-baseline.md](secure-coding-baseline.md): a preamble that classifies the work, then fourteen rules ordered by risk—the first four non-negotiable—and a closing review-and-report step. The rules span access control, untrusted input, secrets and default credentials, preserving controls, secure defaults, authentication abuse resistance, privilege separation, proven mechanisms, dependencies, errors and logging, resource limits, dev-vs-production, abuse tests, and LLM-powered features.

Before completion, the assistant reviews its diff and reports concrete findings—including fixed issues—plus affected controls, test results, and unresolved risks or gaps.

## Using it

Tools load instructions from fixed locations. Apply the same baseline to one project, your machine or account, or an organization.

### Keep the baseline as a separate file

If a tool can be instructed to read another repository file, add this to its normal project-instructions file:

```markdown
Before making any code changes, read `secure-coding-baseline.md` in this repository and follow all rules defined there.
```

This is an instruction to read the file, not a native import; Claude Code's `@` syntax below is the exception.

### Claude Code

Claude Code can import the baseline directly.

- **Project:** put `secure-coding-baseline.md` in the repo and import it from the project `CLAUDE.md`:

  ```markdown
  # CLAUDE.md
  @secure-coding-baseline.md
  ```

- **Your machine:** do the same import from `~/.claude/CLAUDE.md`, pointing at an absolute path:

  ```markdown
  @/absolute/path/to/secure-coding-baseline.md
  ```

- **Organization:** deploy it as a managed-policy `CLAUDE.md`; managed settings or plugins can add enforceable controls. See the [Claude Code organization setup](https://code.claude.com/docs/en/admin-setup).

### GitHub Copilot

Copilot instruction support varies by surface. Copy the baseline into `.github/copilot-instructions.md` for broad repository coverage.

- **Project:** copy them into `.github/copilot-instructions.md`. If the file already exists, append instead of overwriting so existing instructions are preserved:

  ```bash
  mkdir -p .github
  # New file:
  cp secure-coding-baseline.md .github/copilot-instructions.md
  # Existing file — append the baseline:
  cat secure-coding-baseline.md >> .github/copilot-instructions.md
  ```

- **Keep it as a separate file (most surfaces):** place the baseline as its own path-specific instructions file so it loads automatically without touching an existing `copilot-instructions.md`:

  ```bash
  mkdir -p .github/instructions
  { printf -- '---\napplyTo: "**"\n---\n'; cat secure-coding-baseline.md; } \
    > .github/instructions/secure-coding.instructions.md
  ```

  `applyTo: "**"` applies it repository-wide. Path-specific `.github/instructions/**/*.instructions.md` files are supported by the Copilot cloud agent and most Chat and code-review surfaces, but not all (for example, Eclipse Chat reads only `copilot-instructions.md`). For guaranteed coverage everywhere, use `copilot-instructions.md` above.

- **Your account:** paste it into personal custom instructions for Copilot Chat on GitHub.
- **Organization:** paste it into organization custom instructions (Organization settings → Copilot → Custom instructions). Applies only to GitHub.com surfaces—Chat, code review, and the coding agent—not the IDE, which still needs the repository file above. See [organization custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-organization-instructions) and the [support matrix](https://docs.github.com/en/copilot/reference/custom-instructions-support).

### OpenAI Codex

Codex reads `AGENTS.md` automatically but cannot import the baseline.

- **Project:** copy the rules into `AGENTS.md` at the repo root. If the file already exists, append instead of overwriting so existing agent instructions are preserved:

  ```bash
  # New file:
  cp secure-coding-baseline.md AGENTS.md
  # Existing AGENTS.md — append the baseline:
  cat secure-coding-baseline.md >> AGENTS.md
  ```

  Codex has no import directive and loads at most one instruction file per directory (`AGENTS.override.md`, then `AGENTS.md`, then configured fallback names). To keep the baseline as its own file where **no** `AGENTS.md` exists, register it as a fallback name in `~/.codex/config.toml` (`project_doc_fallback_filenames = ["secure-coding-baseline.md"]`). Because only one file per directory is used, this does not combine with an existing `AGENTS.md`—there, append as above.

- **Your machine:** put them in `~/.codex/AGENTS.md`.
- **Organization:** distribute a global `AGENTS.md` through endpoint management or include project `AGENTS.md` files in repository templates. Keep enforceable runtime policy separate in managed configuration. See the [Codex `AGENTS.md` guide](https://developers.openai.com/codex/guides/agents-md/) and [admin rollout guide](https://developers.openai.com/codex/enterprise/admin-setup/).

### Keeping the copies in sync

Keep `secure-coding-baseline.md` as the source of truth and generate copied instruction files from it to prevent drift. An organization template can provide those files to new repositories.

## Background

[Scheurer, Balesni, and Hobbhahn (2024)](https://arxiv.org/abs/2311.07590) show that instructions can reduce, but not eliminate, undesirable behavior in a pressured scenario. [Wallace et al. (2024)](https://arxiv.org/abs/2404.13208) describe how instruction-hierarchy training can improve robustness.

## License

Licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You are free to use, share, and adapt this material for any purpose, including commercially, provided you give appropriate credit. See [LICENSE](LICENSE) for the full terms.
