---
name: secure-coding-baseline-installer
description: Install, check, or safely update the AI Secure Coding Baseline from its official GitHub upstream without an AppSec plugin or repository checkout. Use for project-level or user-wide baseline setup and version checks; do not use it as an application security review workflow.
---

# Secure Coding Baseline Installer

Use the bundled deterministic installer. It accepts baseline content only from
`https://github.com/appsec-foundry/ai-secure-coding-baseline`, validates the
repository, immutable commit reference, format, baseline ID, and size, and never
downloads or executes remote code.

Resolve `scripts/install.py` relative to this `SKILL.md`; do not assume the
user's current directory contains the skill.

## Workflow

Run `status` first. It is read-only and shows the exact upstream source,
available baseline ID, local state, and tool integrations:

```bash
python3 <skill-directory>/scripts/install.py status --into <project>
python3 <skill-directory>/scripts/install.py status --user
```

When the user asked to install, run `install` for the requested scope. Omit tool
names to configure every supported tool in that scope, or pass any of `claude`,
`codex`, and `copilot` after the action:

```bash
python3 <skill-directory>/scripts/install.py install --into <project>
python3 <skill-directory>/scripts/install.py install codex --user
```

When the user asked to update, run `update` for the requested scope:

```bash
python3 <skill-directory>/scripts/install.py update --into <project>
python3 <skill-directory>/scripts/install.py update --user
```

The updater always backs up replaced content. If upstream and local content use
the same baseline ID but differ, stop and show that state. Use
`--backup-and-replace` only after the user explicitly approves replacing that
local variation. Never alter an existing unrelated instruction file or
symlink; report the manual import or link needed instead.

After an install or update, explain that already-running agent sessions retain
their prior instructions. Recommend starting a fresh session and asking
`baseline?` to verify the loaded ID and source file.
