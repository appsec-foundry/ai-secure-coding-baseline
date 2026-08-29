# Surface material baseline security decisions

## Problem

`AISEC-OM-004` and `AISEC-OM-005` require informed confirmation but do not
require the confirmation request to say that it comes from the AISEC baseline.
The baseline can also add or strengthen a control, choose a safer path, or
refuse part of a request without making its influence visible to the user. The
baseline-attributed security note appears only for a material risk left in the
delivered result, so it does not cover these decisions.

The user's Flask example exposes a related trigger gap. A request for HTTP
Basic authentication in an interactive browser application received neither a
warning nor a confirmation request. RFC 7617 describes Basic as carrying a
reusable user-id and password, and RFC 7235 notes that an origin server cannot
reliably make a user agent discard cached credentials. Even with required TLS,
that is materially riskier for browser login than an established server-side
session or managed OIDC flow.

## Goal

Identify the AISEC baseline as the reason when it materially directs the work
for security. Give one concise notice for a related set of decisions in the
first response after the effect becomes clear, and include it in a required
confirmation request before doing work that depends on the user's choice. A
greenfield application whose controls come from the baseline is one such set.
Make browser Basic authentication an explicit riskier-design trigger so this
security best-practice decision does not depend on model recall.

## Non-goals

Do not add notices for checks that found nothing or ordinary work that the
baseline did not materially direct. Do not repeat the notice for each related
control, change the general confirmation threshold, change which acts remain
refusals, or change which risks belong in the **Security note (AISEC baseline)**.
Do not ban Basic authentication or apply the browser-login rule to non-browser
clients without the same interactive-session requirements.

## Compatibility

Affected responses gain one concise source attribution. Implementations and
other security-control requirements stay unchanged. Tools without
intermediate-update support give the notice in their first available response.

An interactive browser application that selects Basic authentication now pauses
for informed design confirmation. After confirmation it may keep Basic over the
transport required by the baseline and records the accepted risk.
