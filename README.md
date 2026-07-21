# AI Secure Coding Baseline

Secure-coding rules for AI coding assistants — the baseline Claude Code, Copilot, and Codex follow when they write and change code.

## Why

AI coding assistants make predictable security mistakes. They add auth bypasses to make tests pass, invent package names, echo secrets into logs, skip input validation, and leak stack traces to clients. They also over-reach — rewriting working code you never asked them to touch.

This baseline is a short set of rules that steers them away from both. It is written for real, existing codebases: it applies only to the code the assistant writes or changes, it flags pre-existing issues instead of silently rewriting them, and it reuses whatever security mechanisms the project already has.

## The rules

The full baseline is in **[ai-secure-coding-baseline.md](ai-secure-coding-baseline.md)** — eleven rules, risk-ordered, the first four non-negotiable:

Access Control · Untrusted Input · Secrets · Preserve Security · Secure by Default · Privilege Separation · Proven Mechanisms · Dependencies · Errors & Logging · Resource Limits · Production vs. Test

Two rules at the top set the boundaries for existing projects: **Scope** (only touch what your change touches) and **Flag, don't fix** (report pre-existing issues, don't silently rewrite them).

## Integration

Same content, three tools. Each reads instructions from a fixed path in the repo — copy the baseline into that path.

### Claude Code

Claude Code can reference the file directly. Copy `ai-secure-coding-baseline.md` into the repo and import it from `CLAUDE.md`:

```markdown
# CLAUDE.md
@ai-secure-coding-baseline.md
```

For all your projects, put the same import in `~/.claude/CLAUDE.md`. For a whole organization, deploy it as managed policy via MDM.

### GitHub Copilot

Copilot reads `.github/copilot-instructions.md` automatically. It cannot import another file, so paste the rules in:

```bash
mkdir -p .github
cp ai-secure-coding-baseline.md .github/copilot-instructions.md
```

For every repo in an organization, set the same content as **Organization custom instructions** in your GitHub Copilot settings.

### OpenAI Codex

Codex reads `AGENTS.md` from the repo root automatically. It cannot import another file, so paste the rules in:

```bash
cp ai-secure-coding-baseline.md AGENTS.md
```

For all your projects, put the same content in `~/.codex/AGENTS.md`.

## This is guidance, not enforcement

An instructions file biases what an assistant generates — it does not guarantee it. Pair the baseline with a security review on the diff (a CI check, or a review pass before merge) so something actually blocks when a rule is missed. The file prevents at write time; the review catches what slips through.
