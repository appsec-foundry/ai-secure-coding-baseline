# AI Secure Coding Baseline

A short set of secure-coding rules for AI coding assistants. Drop it into a project and Claude Code, Copilot, or Codex will follow it when they write or change code.

## Why this exists

AI assistants are useful, but they cut security corners in fairly predictable ways. They'll disable a check to get a test green, import a package that doesn't exist, log a secret, trust input that came straight from a user, or hand back a raw stack trace. They also tend to overreach: ask for a small change and they'll quietly rewrite working code around it.

This baseline pushes back on that. It's written for codebases that already exist, so it stays narrow. It only covers the code the assistant actually writes or changes. It points out pre-existing problems instead of fixing them behind your back. And it reuses whatever security mechanisms the project already has rather than inventing new ones.

## What it helps with

Modern coding assistants often make sensible security choices on their own. Still, without clear project guidance, they are less likely to apply those choices consistently—especially when a task is urgent, ambiguous, or asks them to change existing code. This baseline gives the assistant a shared, concrete set of expectations while it works.

It improves the odds of a secure change; it does not guarantee one. Keep normal security controls in place, including review of the actual diff before merge.

## The rules

The full text is in [ai-secure-coding-baseline.md](ai-secure-coding-baseline.md). Thirteen rules, ordered by risk, with the first four marked non-negotiable:

Access control, untrusted input, secrets and default credentials, preserving existing controls, secure defaults and platform protections, authentication abuse resistance, privilege separation, proven mechanisms, dependencies, errors and logging, resource limits, separating development from production, and security tests with representative negative or abuse cases.

Before completion, it also requires a review of the changed diff against the baseline. The assistant must actively report every concrete security issue found, including fixed issues; for security-relevant changes it also reports affected controls, test results, and unresolved risks or verification gaps.

## Optional AI application add-on

For a project that builds LLM-powered features, also load [ai-secure-coding-ai-add-on.md](ai-secure-coding-ai-add-on.md). It covers AI-specific risks such as prompt injection, tool authorization, action limits, memory isolation, and the OWASP LLM and Agentic Top 10 reviews. Do not load it for ordinary projects that only use an AI assistant to write code.

The baseline first distinguishes two operating modes. For an *existing application*, it keeps the assistant to the code a change touches and has it report concrete pre-existing issues without silently rewriting surrounding code or turning the task into a repository-wide audit. For *greenfield work*, the assistant establishes applicable controls across the new application or component and verifies them before its first production release.

## Using it

Every tool loads its instructions from fixed locations. You can apply the baseline at three levels: a single project, your own machine (so it covers all your projects), or a whole organization. The content is the same in each case.

### Keep the baseline as a separate file

If you want to keep `ai-secure-coding-baseline.md` as the single, separate file in a project, add this instruction to the project's normal AI-instructions file:

```markdown
Before making any code changes, read `ai-secure-coding-baseline.md` in this repository and follow all rules defined there.
```

This works for any coding assistant whose project instructions can tell it to read a repository file. Use the tool's usual instruction file (for example, `CLAUDE.md`, `.github/copilot-instructions.md`, or `AGENTS.md`). It is an instruction to read the file, not a native file import; Claude Code's `@` import below is the exception.

### Claude Code

Claude Code can pull the file in with an `@` import, so you don't have to copy it around.

- **Project:** put `ai-secure-coding-baseline.md` in the repo and import it from the project `CLAUDE.md`:
  ```markdown
  # CLAUDE.md
  @ai-secure-coding-baseline.md
  ```
- **Your machine:** do the same import from `~/.claude/CLAUDE.md`, pointing at an absolute path:
  ```markdown
  @/absolute/path/to/ai-secure-coding-baseline.md
  ```
- **Organization:** there are two ways to roll it out centrally. Push it as managed policy through your MDM, which people can't override, or package it as a plugin and share it through an internal marketplace. The [official docs](https://docs.claude.com/en/docs/claude-code) have the exact file paths and commands.

### GitHub Copilot

Copilot picks up its instructions on its own, but it can't import another file, so the rules have to live in its file directly.

- **Project:** copy them into `.github/copilot-instructions.md`:
  ```bash
  mkdir -p .github
  cp ai-secure-coding-baseline.md .github/copilot-instructions.md
  ```
- **Your account:** paste them into your personal custom instructions in the Copilot settings.
- **Organization:** add the same text as organization (or enterprise) custom instructions in the Copilot admin settings. It then applies to everyone across all repositories, with no per-repo file. This is the cleanest central option of the three tools.

### OpenAI Codex

Codex reads `AGENTS.md` automatically, and like Copilot it can't import another file.

- **Project:** copy the rules into `AGENTS.md` at the repo root:
  ```bash
  cp ai-secure-coding-baseline.md AGENTS.md
  ```
- **Your machine:** put them in `~/.codex/AGENTS.md`.
- **Organization:** there's no admin-pushed rules channel yet, so the practical route is a template repository that new projects inherit `AGENTS.md` from.

### Keeping the copies in sync

Only Claude Code can point at a shared file. For Copilot and Codex the text is copied in, so you can end up with several copies to keep aligned. If that happens, keep `ai-secure-coding-baseline.md` as the single source and generate the others from it, so they can't drift apart. For new repositories, an organization template is the easiest way to start them off with the files already in place.

## Don't rely on it alone

Use this baseline as one layer, not the only one. A review of the actual diff—either in CI or before merge—is the independent control that can catch and stop a bad change.

For background, [Scheurer, Balesni, and Hobbhahn (2024)](https://arxiv.org/abs/2311.07590) show that instructions can reduce, but not eliminate, undesirable behavior in a pressured scenario. [Wallace et al. (2024)](https://arxiv.org/abs/2404.13208) describe how training models to respect an instruction hierarchy can improve their robustness.
