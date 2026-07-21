# AI Secure Coding Baseline

A short set of secure-coding rules for AI coding assistants. Drop it into a project and Claude Code, Copilot, or Codex will follow it when they write or change code.

## Why this exists

AI assistants are useful, but they cut security corners in fairly predictable ways. They'll disable a check to get a test green, import a package that doesn't exist, log a secret, trust input that came straight from a user, or hand back a raw stack trace. They also tend to overreach: ask for a small change and they'll quietly rewrite working code around it.

This baseline pushes back on that. It's written for codebases that already exist, so it stays narrow. It only covers the code the assistant actually writes or changes. It points out pre-existing problems instead of fixing them behind your back. And it reuses whatever security mechanisms the project already has rather than inventing new ones.

## The rules

The full text is in [ai-secure-coding-baseline.md](ai-secure-coding-baseline.md). Eleven rules, ordered by risk, with the first four marked non-negotiable:

Access control, untrusted input, secrets, preserving existing controls, secure defaults, privilege separation, proven mechanisms, dependencies, errors and logging, resource limits, and keeping test bypasses out of production.

Two rules at the top are what make it safe to use on an existing project. *Scope* keeps the assistant to the code your change touches. *Flag, don't fix* tells it to report a pre-existing issue in a line or two and move on, instead of going off and rewriting things.

## Using it

Every tool loads its instructions from fixed locations. You can apply the baseline at three levels: a single project, your own machine (so it covers all your projects), or a whole organization. The content is the same in each case.

### Claude Code

Claude Code can pull the file in with an `@` import, so you don't have to copy it around.

- **Project** — put `ai-secure-coding-baseline.md` in the repo and import it from the project `CLAUDE.md`:
  ```markdown
  # CLAUDE.md
  @ai-secure-coding-baseline.md
  ```
- **Your machine** — do the same import from `~/.claude/CLAUDE.md`, pointing at an absolute path:
  ```markdown
  @/absolute/path/to/ai-secure-coding-baseline.md
  ```
- **Organization** — to enforce it centrally, ship a `managed-settings.json` through your MDM (on Linux that's `/etc/claude-code/managed-settings.json`; see the [official docs](https://docs.claude.com/en/docs/claude-code) for the macOS and Windows paths). You can also package the baseline as a plugin and hand it out through an internal marketplace, which people add once with `/plugin marketplace add <your-repo>`.

### GitHub Copilot

Copilot picks up its instructions on its own, but it can't import another file, so the rules have to live in its file directly.

- **Project** — copy them into `.github/copilot-instructions.md`:
  ```bash
  mkdir -p .github
  cp ai-secure-coding-baseline.md .github/copilot-instructions.md
  ```
- **Your account** — paste them into your personal custom instructions in the Copilot settings.
- **Organization** — set the same text as organization (or enterprise) custom instructions in the Copilot admin settings. That covers every member across all repositories without a per-repo file, and it's the cleanest central option of the three tools.

### OpenAI Codex

Codex reads `AGENTS.md` automatically, and like Copilot it can't import another file.

- **Project** — copy the rules into `AGENTS.md` at the repo root:
  ```bash
  cp ai-secure-coding-baseline.md AGENTS.md
  ```
- **Your machine** — put them in `~/.codex/AGENTS.md`.
- **Organization** — there's no admin-pushed rules channel yet, so the practical route is a template repository that new projects inherit `AGENTS.md` from.

### Keeping the copies in sync

Only Claude Code can point at a shared file; for the others the text is duplicated. If you end up with several copies, treat `ai-secure-coding-baseline.md` as the source and generate the rest from it in CI or a pre-commit hook, writing the source commit into each generated file so you can tell when one has gone stale. New repos are easiest to handle with an organization template.

## Don't rely on it alone

An instructions file changes what an assistant tends to write, but it can't guarantee anything — the model still makes the call. So use it as the first layer, not the only one. Put a security review on the actual diff, either in CI or as a step before merge, so there's something that can genuinely stop a bad change. The baseline helps while the code is being written; the review is what catches whatever slips past it.
