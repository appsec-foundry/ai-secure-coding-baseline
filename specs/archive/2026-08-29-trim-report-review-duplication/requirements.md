# Requirements

## TRIM-001 The diff inspection names the bind among reachable surfaces

Source: the user's explicit request in this conversation to remove the
duplicated sentence after a review of the `Before Completion` section, together
with the verification behind it: the second sentence of the first sub-bullet
repeats the credential and transport checks of the first, and every bind or
loopback check under `tests/cases` belongs to `AISEC-DEFAULTS-001` rather than to
this review duty.

When inspecting the diff, an assistant determines what becomes reachable
including binds, and whether authentication, authorization, and transport cover
it. The duty holds for every change; it is not restricted to an application or
service.

Acceptance: the first sub-bullet of `AISEC-REPORT-001` lists binds among the
reachable surfaces and states the credential, reachability, and coverage checks
once, without a second sentence repeating them.

Example: a change that opens a listener on a non-loopback interface is caught by
the reachability check of the first sentence, whether or not the work is
classified as an application or a service.
