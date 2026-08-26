# Requirements

## LLM-OUTPUT-001 Validate structured output strictly

Source: the user's explicit request in this conversation to validate structured
LLM output, including JSON, identifiers, enums, and numbers, with schemas, type
and range checks, and allow-lists.

Before downstream use, an assistant must make model-controlled structured
output pass deterministic validation against a strict schema and applicable
allow-lists. Unknown, extra, invalid, or ambiguous fields and values must fail
closed.

Acceptance: generated code checks the complete expected structure, types,
ranges, identifiers, and enumerated values without relying on another LLM as
the only validator, and rejects output outside that contract.

## LLM-OUTPUT-002 Render output safely

Source: the user's explicit request in this conversation to use context-aware
output encoding and sanitization for LLM output rendered as HTML, Markdown, or
UI content.

An assistant must contextually encode model output used as text. When markup is
intentionally rendered, it must use a maintained allow-list sanitizer before
display.

Acceptance: model-controlled content cannot create active markup, scripts,
event handlers, or unsafe links merely by reaching a browser or UI renderer.

## LLM-OUTPUT-003 Use parameterized APIs or isolation

Source: the user's explicit requests in this conversation not to execute LLM
output directly and to ensure that LLM integrations use parameterization
through the corresponding API.

An assistant must pass validated model-controlled values only as data through
the sink's parameterized API. It must not concatenate them into queries,
commands, code, or tool instructions or pass them directly to an interpreter.
If executing generated code is the intended feature, execution must occur in an
isolated sandbox with filesystem, network, time, and resource restrictions.

Acceptance: SQL uses bound parameters, process execution uses a fixed
executable and separated arguments without a shell, tool calls use validated
typed arguments and allow-listed operations, and generated code is either not
executed or confined to the required sandbox.

## LLM-OUTPUT-004 Bind resources and actions

Source: the user's explicit request in this conversation to validate and
allow-list model-selected URLs, paths, tool calls, and object identifiers and
to enforce authorization and ownership.

An assistant must apply the baseline's validation, safe-path, destination,
server-side authorization, ownership, and least-privilege controls to every
resource and action selected through model output.

Acceptance: a valid model response still cannot select an arbitrary
destination, escape an allowed path, invoke an unapproved operation, or access
a resource outside the authenticated principal's authority.

## LLM-OUTPUT-005 Add model evidence

Source: the user's explicit request in this conversation to implement the
recommended output-validation coverage after verification.

The model suite must exercise `AISEC-LLM-001` with structured output,
rendering, a parameterized downstream API, and a model-selected protected
resource or action.

Acceptance: the case can detect permissive schemas, unsafe rendering, string
construction at a downstream sink, and missing authorization or ownership
checks, and the readable catalog states what remains untested.
