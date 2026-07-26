# AI Secure Coding Baseline

[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](#)
[![Last commit](https://img.shields.io/github/last-commit/matthiasrohr/ai-secure-coding-baseline.svg)](https://github.com/matthiasrohr/ai-secure-coding-baseline/commits)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-compatible-D97757?logo=anthropic&logoColor=white)](https://code.claude.com/)
[![GitHub Copilot](https://img.shields.io/badge/GitHub%20Copilot-compatible-000000?logo=githubcopilot&logoColor=white)](https://github.com/features/copilot)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI%20Codex-compatible-412991?logo=openai&logoColor=white)](https://developers.openai.com/codex/)

A short set of secure-coding rules for AI coding assistants. Add it to a project's instructions and Claude Code, Copilot, or Codex will follow it when they write or change code.

> **Status: Beta.** Still refining the rules and their wording, so expect changes. No stable version tagged yet.

> **Limitations**
>
> This baseline guides an LLM; it is not an enforceable control or a guarantee of secure code. Supplement it with project-specific instructions and independently validate changes through review, tests, dependency and secret scanning, SAST, and CI or pre-commit checks as appropriate.

The baseline is deliberately compact: ~11.0 KB (roughly 2,900 model tokens), including one condensed rule for LLM-powered features. Counts vary by tokenizer. The wording has been reviewed and refined through AI-assisted coding tasks—practical testing, not a formal security certification.

## Why this exists

Modern AI coding assistants get a lot right, but they do not apply security requirements consistently. [Yan et al. (2025)](https://arxiv.org/abs/2506.23034) find that models are prone to generating insecure code yet produce safer code once security expectations are made explicit, suggesting a gap between knowing secure practices and reliably using them.

That gap matters most under pressure. When the goal becomes “make the test pass” or “finish quickly,” assistants are more likely to take unsafe shortcuts, such as weakening checks, skipping validation, or introducing risky dependencies. [Chen et al. (2026)](https://arxiv.org/abs/2604.20200) show this with AgentPressureBench, where repeated user pressure to raise a score induces shortcut behavior across every task, and [Scheurer, Balesni, and Hobbhahn (2023)](https://arxiv.org/abs/2311.07590) show the same pattern outside coding.

## Covered risks

This is a compact guardrail, not a complete standard or compliance checklist. It addresses:

- **Common application risks:** major classes also represented in the [OWASP Top 10:2025](https://owasp.org/Top10/2025/), including access control, misconfiguration, supply-chain and integrity failures, cryptography, injection, insecure design, authentication, logging, and error handling.
- **AI-assisted coding risks:** package hallucinations and slopsquatting through independent, current verification instead of model confidence or package existence alone, plus unsafe scope expansion and weakened controls. See the [OWASP npm Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html#slopsquatting-attacks).
- **Dependency supply chains:** unnecessary or unverified packages, unexpected transitive changes, unreviewed install scripts, missing lockfiles, non-reproducible builds, and absent dependency scanning.
- **LLM application risks:** prompt injection, unsafe model output and tool use, excessive agency, and data or memory exposure—covered by one condensed rule in the baseline—reviewed against the [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) and [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).

## The rules

The full text is in [secure-coding-baseline.md](secure-coding-baseline.md): a preamble that classifies the work, then thirteen rules ordered by risk—the first four non-negotiable—and a closing review-and-report step. The rules span access control, untrusted input, secrets and default credentials, preserving controls, secure defaults, authentication abuse resistance, proven mechanisms, dependencies, errors and logging, resource limits, dev-vs-production, abuse tests, and LLM-powered features.

Before completion, the assistant reviews its diff and reports concrete findings—including fixed issues—and closes with a short security note covering affected controls, test results, and unresolved risks or gaps, even when none remain.

## Using it

Every tool loads project instructions from its own fixed locations, so installing the baseline means putting it where the tool already looks. Three cases cover the field: **Claude Code**, which reads only its own files; **GitHub Copilot**, which uses its own locations on several surfaces; and **every other agent**, which reads the shared [`AGENTS.md`](https://agents.md/).

Keep `secure-coding-baseline.md` as the one real file and reference it from each location. Claude Code can import it directly, most other tools need a symlink, and only where neither works should you copy—every copy is a chance to drift. Each mechanism works the same way for a single project, for your machine or account, and for an organization.

### Claude Code

Claude Code does **not** load `AGENTS.md`. Checked against v2.1.220: project instruction discovery covers `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, and `.claude/rules/`, plus `~/.claude/CLAUDE.md` and managed policy. `AGENTS.md` appears in the binary only in the Codex-migration importer, which copies it to `CLAUDE.md`, and in the `/init` prompt.

It may still open the file as ordinary content if a task leads it there—but that is a choice, not a guarantee, so an `AGENTS.md` alone leaves the rules out of context on any prompt that does not go looking for them.

- **Project:** put `secure-coding-baseline.md` in the repo and import it from the project `CLAUDE.md`. This is a real import—no copy, no drift:

  ```markdown
  # CLAUDE.md
  @secure-coding-baseline.md
  ```

  Where an `AGENTS.md` already carries the rules, import that instead with `@AGENTS.md`.

- **Project, without a `CLAUDE.md`:** put the baseline at `.claude/rules/secure-coding-baseline.md`; files there load automatically, and a symlink to the real file works.

- **Your machine:** do the same import from `~/.claude/CLAUDE.md`, pointing at an absolute path:

  ```markdown
  @/absolute/path/to/secure-coding-baseline.md
  ```

- **Organization:** deploy it as a managed-policy `CLAUDE.md`; managed settings or plugins can add enforceable controls. See the [Claude Code organization setup](https://code.claude.com/docs/en/admin-setup).

#### Verify it loaded

An instruction file that is never loaded fails silently—the assistant behaves as if the rules do not exist, and nothing reports the gap. Check before relying on it:

- `/context` — the *Memory Files* table lists every loaded file with its token count.
- `/memory` — lists loaded files, including resolved `@` imports.
- `claude --debug` — logs instruction-file discovery and import resolution at startup.
- After the fact: `grep -c "Non-negotiable" ~/.claude/projects/<project-slug>/<session-id>.jsonl`. A `0` means the baseline was never in context.

### GitHub Copilot

Copilot's coding agent and VS Code are on the agents.md list, so the root `AGENTS.md` described [below](#every-other-agent) already covers them. The remaining surfaces read Copilot's own locations, and support varies; `.github/copilot-instructions.md` is the most broadly supported.

- **Project:** copy the baseline into `.github/copilot-instructions.md`. If the file already exists, append instead of overwriting so existing instructions are preserved:

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

### Every other agent

Everything that is not Claude Code reads [`AGENTS.md`](https://agents.md/), an open format stewarded by the Agentic AI Foundation under the Linux Foundation. Per the [compatibility list](https://agents.md/) that covers Codex, Cursor, Gemini CLI, GitHub Copilot's coding agent, VS Code, Devin, Jules, Junie, Factory, Amp, Zed, Warp, Aider, goose, opencode, Windsurf, RooCode, Kilo Code and others. Support is declared per tool, not guaranteed by the format—confirm it on the surfaces you actually use.

`AGENTS.md` is plain Markdown with no import directive; nested files in subdirectories are its only composition mechanism. To avoid a second copy, symlink it, the approach the [agents.md FAQ](https://agents.md/) itself suggests for reusing an existing file:

```bash
# One file on disk, two names:
ln -s secure-coding-baseline.md AGENTS.md
```

Git stores the symlink, so clones get it too—but a Windows checkout without Developer Mode or `core.symlinks=true` silently turns it into a text file containing the target path, and the rules never load. Verify after cloning, or copy instead on Windows:

```bash
# New file:
cp secure-coding-baseline.md AGENTS.md
# Existing AGENTS.md — append the baseline:
cat secure-coding-baseline.md >> AGENTS.md
```

Where an `AGENTS.md` already exists, a symlink cannot merge with it—append, as above.

**Codex** needs nothing beyond the root file, with two additions. It loads at most one instruction file per directory (`AGENTS.override.md`, then `AGENTS.md`, then configured fallback names), so where **no** `AGENTS.md` exists you can skip the symlink and register the baseline's own filename in `~/.codex/config.toml` instead: `project_doc_fallback_filenames = ["secure-coding-baseline.md"]`. For your machine, use `~/.codex/AGENTS.md`; for an organization, distribute a global `AGENTS.md` through endpoint management or ship project `AGENTS.md` files in repository templates, keeping enforceable runtime policy separate in managed configuration. See the [Codex `AGENTS.md` guide](https://developers.openai.com/codex/guides/agents-md/) and [admin rollout guide](https://developers.openai.com/codex/enterprise/admin-setup/).

**Tools that read no shared format** can often still be told to read a repository file. Add this to whatever project-instructions file they do read:

```markdown
Before making any code changes, read `secure-coding-baseline.md` in this repository and follow all rules defined there.
```

This is an instruction to read the file, not a native import—the assistant must choose to follow it. Claude Code's `@` syntax is the only real import among these tools.

### Keeping the copies in sync

Prefer an import, symlink, or registered filename so there is only ever one copy. Where a tool supports none of these, keep `secure-coding-baseline.md` as the source of truth and generate the copied instruction files from it rather than editing them by hand. An organization template can provide those files to new repositories.

## Testing the baseline

`tests/` holds a harness that runs the same prompt with the baseline installed and without it, and reports the difference. Cases cover greenfield work, scoped changes to an existing application, pressure to weaken a control, and overrides in both directions.

```bash
make check                                         # validate the cases, no model calls
python3 tests/run.py --cases greenfield-order-app  # one case, both arms
```

Runs cost tokens and time; at affordable sample sizes the results show direction rather than significance. See [tests/README.md](tests/README.md).

## Background

Whether project instructions change what an assistant does is contested, and the evidence splits in a way worth knowing before relying on them. [Gloaguen et al. (2026)](https://arxiv.org/abs/2602.11988) evaluated repository context files on real tasks and found they do not make agents better at their work—but the same study found that explicit instructions in those files are followed. What does not pay off are the repository overviews most templates lead with. On security specifically, [Kharma et al. (2026)](https://arxiv.org/abs/2605.24298) found that security-aware prompting alone did not significantly reduce how many vulnerabilities a model produced, only which ones. So the realistic claim for a baseline like this is narrow: it changes what the assistant treats as required. It does not guarantee secure code.

Where it earns its place is under pressure. In the AgentPressureBench study cited above, agents pushed to keep improving a score cut corners on every task, and the harder the push, the sooner they started. When the researchers added explicit rules against exactly that, the behavior nearly disappeared—from 100% down to 8.3%. Written rules clearly help; the remaining 8.3% is why this one is a guardrail and not a control. The same caution applies over time: [Shukla et al. (2025)](https://arxiv.org/abs/2506.11022) saw critical vulnerabilities climb after just five rounds of asking a model to improve its own code, and [Gamage (2026)](https://arxiv.org/abs/2604.20911) found that prohibitions lose their grip as a session grows long, while positively phrased requirements hold. Rules read once at the start are weakest late in a long session—which is part of why the baseline ends with a review-and-report step instead of trusting the rules alone. [Wallace et al. (2024)](https://arxiv.org/abs/2404.13208) point at the durable fix: instruction-hierarchy training, which works at the model level rather than the file level.

## License

Licensed under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You are free to use, share, and adapt this material for any purpose, including commercially, provided you give appropriate credit. See [LICENSE](LICENSE) for the full terms.
