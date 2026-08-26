# Validate LLM output at downstream boundaries

## Problem

`AISEC-LLM-001` says to validate model output, but it does not name the
mechanisms needed for structured output, rendered markup, parameterized APIs,
or intentional code execution. An assistant can therefore satisfy the wording
with a weak format check and still pass model-controlled data to a dangerous
sink.

## Goal

Require strict deterministic validation of structured LLM output, safe
rendering, sink-specific parameterized APIs, and isolation when executing code
is the intended feature. Preserve the existing authorization, ownership, path,
and destination controls for model-selected resources and actions.

## Non-goals

Do not prescribe an LLM provider, output-schema library, sanitizer, sandbox
product, or application-specific schema. Do not attempt to detect every prompt
injection or make model output trustworthy.

## Compatibility

LLM features that currently trust syntactically valid JSON, render generated
markup without sanitization, construct executable text, or run generated code
without isolation must adopt the applicable validation or containment
mechanism. The baseline remains provider- and framework-neutral.
