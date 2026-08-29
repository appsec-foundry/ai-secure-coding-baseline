# Requirements

## ATTR-001 Attribute material baseline security decisions

Source: the user's explicit request in this conversation that users be told
when the baseline actively intervenes and materially increases security,
including when it treats an application as greenfield or requires confirmation
of an unsafe design decision.

When following the baseline materially directs the work by treating an
application as greenfield and supplying its controls, taking a safer path,
refusing an act, or requiring confirmation, the assistant must identify the
AISEC baseline as the reason. A check that found nothing and ordinary work the
baseline did not materially direct do not trigger a notice.

Acceptance: affected replies name the AISEC baseline and the concrete decision
it caused; replies do not emit an empty attribution for unchanged work or a
successful check alone.

## ATTR-002 Give the notice at the first response

Source: the user's explicit follow-up request in this conversation that the
notice be given as soon as possible.

The assistant must give the attribution in its first response after the
baseline's material effect becomes clear. If the decision requires user
confirmation, the confirmation request itself carries the attribution and no
work dependent on that choice happens first.

Acceptance: a confirmation case names the AISEC baseline while asking and stops
before implementation; a security control added without a user decision is
attributed in the first reply that reports the result.

## ATTR-003 Keep related notices concise

Source: the user's explicit follow-up request in this conversation that the
notice not become extreme and appear only when the baseline actively intervenes
in an important way, with a greenfield application as the example.

One concise notice must cover a related set of baseline-directed decisions.
The assistant must not repeat the attribution for every control or turn it into
a list of rule IDs.

Acceptance: a greenfield reply may state once that the application is being
built under the AISEC baseline; it does not attach a separate baseline notice
to every authentication, transport, input, or browser control.

## BASIC-001 Flag Basic authentication for browser login

Source: the user's explicit report in this conversation that a request for a
Python and Flask web application with HTTP Basic authentication produced no
baseline warning, together with the user's clarification that the baseline
must steer security best practices rather than cover only forbidden acts.

For interactive browser user authentication, the assistant must treat HTTP
Basic authentication as a materially riskier design than an established
server-side session mechanism or managed OIDC. It must explain the reusable
credential and server-controlled logout or expiry limitations, give the safer
alternative and its integration cost, and apply the Design decisions and
Baseline Attribution rules before proceeding. Basic remains available after
informed confirmation and under the baseline's transport requirements.

Acceptance: the first reply to a browser Basic authentication design names the
AISEC baseline, states the concrete credential and lifecycle risk, offers an
established session or managed OIDC alternative with its cost, asks for explicit
confirmation, and does not implement or finalize the design first.
