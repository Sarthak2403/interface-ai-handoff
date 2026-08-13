# 1. Architecture

The core design separates probabilistic discovery from deterministic production execution.

A discovery agent receives a natural-language goal and observes a browser surface. It proposes typed actions, which pass through schema validation and a safety gate before execution. The discovered action trace is normalized by an artifact compiler into a versioned, parameterized capability. The replay engine consumes only that artifact and never asks an LLM what to do next.

The browser surface is behind a `ComputerSurface` protocol. The current implementation provides a Playwright browser adapter. A desktop adapter could implement the same observation/action contract using an OS accessibility tree or native automation APIs without changing the artifact or replay layers.

The implementation intentionally avoids distributed infrastructure. The assignment values core abstractions over premature scaling infrastructure.

# 2. Artifact schema

The artifact is a typed Pydantic model containing:

- capability identity and schema version
- target application and surface
- parameter definitions
- ordered actions
- locator strategies
- checkpoints
- business outcomes
- safety policy

The artifact is deliberately decoupled from the raw model transcript. A transcript is useful for debugging and evaluation, but it is not a production capability because it contains model-specific reasoning and unnecessary context.

Actions are parameterized. For example, a discovered member ID is represented as `{{member_id}}` rather than permanently embedding `12345`. This allows one successful discovery to become a reusable capability.

Locators are semantic where possible: role, label, or text. Lower-level selectors are available as fallbacks.

# 3. Determinism & error handling

Replay contains no LLM dependency. Each artifact step is executed deterministically against the browser surface, with safety validation applied before browser actions and checkpoints used to verify expected application state.

The system distinguishes three broad classes:

- Business outcomes: expected domain results such as `MEMBER_NOT_FOUND`.
- Runtime/replay failures: conditions such as Playwright timeouts or failed checkpoints.
- Hard application failures: unexpected application states, such as the injected application error for member `50000`.

The demo deliberately includes `99999` as a not-found business outcome and `50000` as an injected application failure.

Checkpoints are essential because a successful click does not prove the application reached the intended state. Replay therefore asserts conditions such as `Member Details` being present before extracting the result.

The design prefers condition-based state verification over arbitrary fixed sleeps. The current demo uses Playwright's built-in action waiting and explicit checkpoint validation; a production implementation would add richer condition-based wait primitives for dynamic applications.

# 4. Heterogeneity & multi-tenant

The `ComputerSurface` abstraction separates automation semantics from a particular UI technology. The current browser implementation uses Playwright. A production implementation could add:

- browser DOM/accessibility adapter
- native desktop accessibility adapter
- screenshot/coordinate adapter for controls unavailable through accessibility APIs

The capability artifact identifies the target application and surface independently from tenant-specific configuration. In production, tenant configuration would select the application instance, credentials/session mechanism, version compatibility, and locator overrides.

The reusable unit is therefore the capability, while tenant configuration describes how that capability is exposed by a particular application instance.

# 5. Escalation & handoff

The replay engine creates an intervention request when it cannot safely continue.The request contains the intervention ID, current step, current URL, failure reason, last successful checkpoint when available, and redacted context. The demo's filesystem-backed manager does not persist a browser session identifier; a production handoff layer would associate the intervention with the live browser session.

The intended handoff boundary is the same live browser session rather than starting a second independent browser. In this demo, the browser is kept headed during escalation while the filesystem-backed intervention record captures the state required for an operator handoff. A production implementation would persist a session identifier and provide an operator resume mechanism. A production operator could then correct the state and explicitly resume the replay boundary. In this demo, the browser is kept headed during escalation while the filesystem-backed intervention record captures the state required for an operator handoff. A production implementation would persist a session identifier and provide an operator resume mechanism. A production implementation would allow a human to correct the state and explicitly resume the replay boundary.

A production operator UI would consume the same intervention record and expose the live session through a controlled remote-browser mechanism. The demo uses a filesystem-backed intervention manager and a headed browser to keep the seam real without spending time on a dashboard.

# 6. Safety

Safety is enforced before browser execution rather than being delegated to the model.

The action gate validates:

- action type
- target domain
- allowed surface operations

Parameterized inputs are resolved by the replay engine before execution.

A production policy would additionally classify financial mutations as requiring human confirmation and would deny destructive or unauthorized actions.

The synthetic application contains no real member data. Operational logs redact sensitive values. The repository contains no credentials.

The main limitation is that the demo safety policy is intentionally small. A production financial system would require tenant-aware authorization, stronger secret isolation, immutable audit records, retention controls, and data classification.

# 7. Cuts

The implementation deliberately cuts:

- native desktop execution
- distributed queues/workers
- real multi-tenant infrastructure
- production authentication
- a full operator dashboard
- broad arbitrary-task discovery

The local Ollama adapter is included as an optional real local-LLM seam without requiring a cloud API key. The default offline planner keeps the entire demo runnable without external services.

With more time, the next additions would be a real operator UI, native desktop surface adapter, richer locator fallback using accessibility trees, artifact compatibility testing across application versions, and tenant-specific locator override resolution.
