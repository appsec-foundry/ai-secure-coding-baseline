# AI Application Security Add-on

**Scope:** Apply these rules only when a change builds or changes an LLM-powered feature. They supplement, not replace, the AI Secure Coding Baseline.

- **Untrusted AI Inputs and Outputs:** Treat prompts, model outputs, retrieved content, tool output, documents, URLs, and agent memory as untrusted data. Validate it before rendering, executing, or passing it to another system. Do not let its instructions or data override application policy, authorization, or task boundaries.
- **Authorization and Tool Access:** Authorize every tool action server-side for the authenticated user and specific resource. Give each tool the minimum permissions and data it needs; do not expose broad credentials or unrestricted shell, network, or data access to a model.
- **Bounded Actions:** Validate tool arguments, allow-list destinations and operations, and limit time, cost, retries, data volume, and side effects. Require explicit human approval before consequential, irreversible, financial, external, or privileged actions.
- **Data and Memory:** Minimize data sent to models and retained in memory; keep tenants and users isolated. Do not store secrets or sensitive data in prompts, logs, vector stores, or long-term memory unless explicitly required and protected.
- **Review:** Review LLM-powered changes against the current OWASP Top 10 for LLM Applications. When an agent can use tools, access data, retain memory, delegate work, or take actions, also review against the OWASP Top 10 for Agentic Applications.
