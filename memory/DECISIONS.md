# Decision Log

Append new decisions. Do not erase history; mark replaced decisions superseded and link the replacement.

Decision record format, conflict classification, approval attribution, expiry, and supersession rules are defined in `docs/architecture/decision-and-approval-protocol.md`.

## ADR-001 — Git-native canonical memory
- Status: accepted | Date: 2026-11-04
- Context: memory must survive provider/session changes and remain portable.
- Decision: project-owned Markdown/JSON committed with the project is canonical.
- Rationale: inspectable, editable, diffable, portable, no hosted dependency.
- Consequence: explicit read/write protocols; indexes are derived and rebuildable.

## ADR-002 — No mandatory database
- Status: accepted | Date: 2026-11-04
- Decision: PostgreSQL/Supabase/vector database is not required for baseline memory.
- Consequence: file schemas and local validation are required; optional retrieval may be added later.

## ADR-003 — Hierarchical authority
- Status: accepted | Date: 2026-11-04
- Decision: USER → ORCHESTRATOR → MANAGERS → SPECIALISTS; Orchestrator alone faces the user.
- Consequence: adapters preserve role boundaries or document sequential fallback.

## ADR-004 — OpenCode first, provider-neutral core
- Status: accepted | Date: 2026-11-04
- Decision: implement OpenCode first behind a provider adapter contract.
- Consequence: verify current official conventions; later adapters may include Claude Code and Cursor.

## ADR-005 — Approval for conflicts and material decisions
- Status: accepted | Date: 2026-11-04
- Decision: Orchestrator pauses for user approval before resolving material conflicts or consequential actions.
- Consequence: explicit conflict/approval workflow and decision records are required.

## ADR-006 — OpenCode V2-native adapter baseline
- Status: accepted | Date: 2026-11-04
- Context: OpenCode V2 is current (`v2.2.5` observed locally); V1 and V2 use different native config shapes, while V2 reads supported V1 configuration.
- Decision: the first adapter generates V2-native agents, commands, skills, and configuration; portable Markdown commands/skills are preferred where practical; V1 limitations are documented rather than claimed as conformance.
- Rationale: aligns with the current provider version, avoids deprecated V1 frontmatter, and preserves a documented migration path.
- Consequence: V2-native permission/agent files are not V1-compatible; adapter conformance claims are explicitly V2-scoped. TASK-009 must revalidate current official documentation before implementation.

## ADR-007 — Opt-in depth-2 hierarchy with sequential fallback
- Status: accepted | Date: 2026-11-04
- Context: OpenCode defaults `subagent_depth` to 1, which prevents a Manager subagent from launching Specialist subagents. V2 exposes depth 2 under `experimental.subagent_depth`.
- Decision: the adapter may enable depth 2 when the user approves it, documents it as an experimental provider dependency, and provides a sequential single-agent fallback when unavailable.
- Rationale: preserves Managers as real coordinators/reviewers without making true nesting mandatory for baseline operation.
- Consequence: adapter conformance must cover both depth-2 (when enabled) and sequential fallback; experimental behavior may change.


## ADR-008 — Provider-neutral observability core with provider-specific monitor UI
- Status: accepted | Date: 2026-11-04
- Context: users need visibility into execution, agent activity, blockers, approvals, and progress without coupling the Blueprint to one coding-agent interface.
- Decision: observability semantics and data contracts belong to the provider-neutral Blueprint core. Provider adapters implement monitor UIs. The first implementation is `developer-ai-init-monitor`, an OpenCode TUI sidebar plugin.
- Ownership/runtime: this Blueprint repository owns and versions the specification and plugin source. The initializer installs/configures it in generated projects. At runtime it reads canonical `.blueprint/` state inside OpenCode; it does not modify OpenCode itself or require a separate service.
- Constraints: the core remains usable without a monitor. The monitor is presentation only, never a second source of truth. OpenCode-specific event handling and sidebar rendering stay in its adapter; other adapters may provide different UIs.
- Consequences: define a provider-neutral observability contract, update/freshness semantics, and degraded mode before implementation. Verify compatibility with OpenCode 2.2.5. See `docs/architecture/ADR-008-provider-neutral-observability.md`.

## ADR-009 — Internal Python tooling without target runtime coupling
- Status: accepted | Date: 2026-11-05
- Context: TASK-020 requires executable regeneration and task-completion validation, while the implementation/package runtime for initialized projects remains undecided.
- Decision: Python 3.9+ standard-library tools may support Blueprint source-repository development, generation, validation, and lifecycle gates. They must not be copied into generated projects or make Python a target-project requirement.
- Rationale: reuse the source repository's existing Python validation convention without imposing an unapproved runtime on target projects.
- Consequence: the source repository owns and tests its Python completion gate; target projects remain runtime-neutral and may use their own previously approved local runtime for executable validation.

## ADR-010 — Python standard-library Blueprint generator
- Status: accepted | Date: 2026-11-05
- Related: TASK-013
- Approval: USER, 2026-11-05, approve Python 3.9+ standard-library tooling only inside Developer AI Init; generated projects do not require Python.
- Context: TASK-013 needs a provider-neutral generator and collision preview. Python was one viable implementation stack; the target-project runtime must remain independent.

### Options
1. Python 3.9+ standard library — reuses repository tooling and tests without dependencies; the host invoking the generator needs Python.
2. TypeScript with Node/Bun — fits the OpenCode adapter ecosystem, but adds a host runtime and can couple the provider-neutral generator to that ecosystem.
3. Go standard library — can be distributed as platform binaries without a runtime, but adds a language and build/release matrix.

### Decision
Implement the TASK-013 generator as Python 3.9+ standard-library tooling in this repository. It runs only on the host executing the Blueprint source tool. Generated projects contain no Python helper or Python runtime requirement.

### Rationale
The user approved this option. It follows ADR-009, reuses the repository's proven generator and test conventions, avoids new dependencies, and keeps core generation separate from OpenCode-specific templates.

### Consequences
A host invoking the source generator needs Python 3.9+; standalone distribution for machines without Python is not part of this decision or TASK-013. This approval remains valid only while the generator is internal and generated projects acquire no Python runtime dependency.

### Approval evidence
The user explicitly approved Python 3.9+ standard-library tooling for internal use in Developer AI Init and specified that generated projects must not need Python.

## ADR-011 — Offline Blueprint validation with Python and jsonschema
- Status: accepted | Date: 2026-11-05
- Related: TASK-014, ADR-009
- Approval: USER, 2026-11-05, approve Python 3.9+ with a pinned `jsonschema` validation dependency for internal validation tooling.
- Context: TASK-014 must validate the repository's Draft 2019-09 schemas accurately, report semantic task/reference issues and secret-like values safely, and run offline.
- Decision: Implement the validator as Python 3.9+ source-repository tooling using a pinned `jsonschema` dependency. Schema references are local-only; validation performs no network access and makes no project-file changes. Provision the dependency before running in a disconnected environment.
- Rationale: Reuse the repository's Python tooling while relying on a standards-aware implementation instead of maintaining a partial JSON Schema engine.
- Consequences: The validation tool requires the pinned development package to be installed; generated projects do not receive Python or this dependency. Validation remains offline after provisioning.
- Approval evidence: The user selected `python-jsonschema` for TASK-014.
