# Protect agentic development work

## Problem

The baseline protects the applications an assistant changes, including
LLM-powered features, but does not explicitly protect the assistant's own work
from instructions embedded in retrieved task content. It also leaves package
version vulnerabilities, executable external references, secret-bearing tool
context, and weakened tests or build configuration implicit.

## Goal

Add compact, tool-neutral mechanisms for untrusted development context,
secret-safe diagnostics, dependency and external-artifact verification, and
review of tests and automatically executed configuration.

## Non-goals

Do not add tool-specific MCP rules, runtime sandbox configuration, organization
governance, SBOM/SAST/DAST mandates, package-popularity heuristics,
language-specific guidance, or constant-time comparison guidance. Do not widen
the application-focused LLM rule to govern the coding agent itself.

## Compatibility

Retrieved content remains usable as task input but cannot become independent
authority. Legitimate changes to assistant instructions, tests, dependencies,
and build or deployment files remain possible when they are in scope and pass
the new review. The normative revision uses the default patch increment and
becomes `aisec-0.1.3`.
