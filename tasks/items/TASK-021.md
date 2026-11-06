# TASK-021 — Add live agent and delegation tracking to the OpenCode monitor

## Metadata
- Status: ready
- Priority: high
- Owner role: MANAGER: Engineering
- Specs: SPEC-006, SPEC-007
- Dependencies: TASK-019
- Created: 2026-11-06
- Updated: 2026-11-06

## Objective
Extend the existing optional OpenCode monitor so a user can see the configured agent hierarchy, the tasks and named work items actually assigned through agent delegation, the observed delegation/review path, and recent runtime activity in one compact view. Combine canonical Blueprint state with verified OpenCode runtime observations without creating a second source of truth or inventing agent/task states.

## Context
- TASK-019 established the provider-neutral observability contract and the optional OpenCode TUI sidebar monitor.
- Existing implementation: `adapters/opencode/monitor/` (`src/index.ts`, `src/blueprint.ts`, `src/tui.tsx`).
- Target runtime for this task: OpenCode v2.2.5.
- The current monitor reads persisted Blueprint records. The plugin entry point does not yet capture runtime agent/delegation events.
- Read `docs/architecture/observability.md`, `docs/architecture/agent-hierarchy.md`, `docs/architecture/task-lifecycle.md`, and the TASK-019 brief before implementation.
- Canonical task status, task names, dependencies, approvals, and configured role definitions remain authoritative in their existing Blueprint files. OpenCode runtime events are authoritative only for runtime sessions and observed invocations.
- A role hierarchy in configuration is not proof that a corresponding runtime agent/session is active. A task owner role is not proof that a task was delegated to a particular agent.

## Scope
1. **Technical discovery**
   - Inspect the installed/declared OpenCode v2.2.5 plugin API and existing monitor implementation.
   - Identify supported lifecycle events/hooks and the fields available to correlate parent/child sessions, agent names, tool invocations, task prompts, timestamps, completion, errors, and interruptions.
   - Verify findings against official/local API types or executable tests; do not infer event semantics from names alone.
   - Document gaps and propose the smallest compatible event-to-observability mapping before relying on it.
2. **Agent hierarchy**
   - Display the configured logical hierarchy and agent roles from canonical configuration.
   - Separately indicate runtime agents/sessions that have actually been observed, including active/finished/failed/interrupted only when supported by evidence.
3. **Tasks and delegation**
   - Show task ID and title from canonical task records.
   - Show responsible agent and named delegated work item only when an actual runtime delegation or canonical assignment provides that information.
   - Show the observed delegation chain (for example Orchestrator → Manager → Specialist → Manager review → Orchestrator) only when the events support each edge.
   - Distinguish assignment, execution, return/completion, review, and approval. Do not infer review or approval from a session ending.
   - Do not fabricate per-agent checklists. Show task acceptance checklists only if they are already available in canonical task briefs; show delegated work-item names only when present in the actual delegation payload.
4. **Recent activity**
   - Present a compact, chronological activity feed for supported events such as delegation, session start/end, completion/return, errors, and review/approval observations.
   - Refresh using supported plugin events and the existing observability refresh model. Avoid excessive polling.
5. **UI and compatibility**
   - Extend the existing optional OpenCode TUI sidebar monitor; do not create a separate dashboard or mandatory service.
   - Keep the view compact and scannable, with task details/delegation chain expandable or otherwise progressively disclosed if needed.
   - Preserve current monitor commands/toggle behavior and existing canonical snapshot functionality.
6. **Evidence**
   - Add focused tests for event mapping, correlation, ordering, duplicate/out-of-order events, missing fields, parallel delegations, failures, and interrupted sessions.
   - Validate with real OpenCode v2.2.5 runtime activity where feasible and record exact reproduction steps and observed output.

## Out of scope
- Changing the canonical task lifecycle, task registry schema, or approval protocol unless a separately approved architecture change proves necessary.
- Making the monitor a source of truth or allowing it to write canonical task, approval, handoff, or memory records.
- Creating a database, hosted service, network dependency, telemetry backend, or external account integration.
- Building agent administration, task assignment, or orchestration controls into the monitor.
- Implementing Claude Code or Cursor monitor UIs.
- Modifying global OpenCode configuration or files outside this repository.
- Installing or modifying the monitor in `blueprint-demo` as part of this task.

## Acceptance criteria
- [ ] **AC-01 — Verified runtime API:** A discovery note documents the OpenCode v2.2.5 event/hooks used, their exact relevant payload fields, correlation limits, and evidence (API types/source references and tests or runtime observations). Unsupported assumptions are explicitly listed.
- [ ] **AC-02 — Honest hierarchy:** The monitor displays the configured logical hierarchy separately from runtime agents/sessions actually observed; it never presents configured agents as active sessions without runtime evidence.
- [ ] **AC-03 — Task and delegation detail:** The monitor displays canonical task ID/title/status and shows agent ownership, delegated work-item name, and delegation edges only when supported by canonical assignment data or correlated runtime evidence. Unknown/unobserved data is labelled clearly rather than inferred.
- [ ] **AC-04 — Lifecycle distinctions:** Assignment/delegation, session execution, return/completion, review, and approval are represented as distinct states/events; session termination alone is not treated as task completion, review, or approval.
- [ ] **AC-05 — Activity feed:** A compact chronological feed displays supported runtime events with stable ordering and useful task/session correlation; duplicate, missing, delayed, or out-of-order events do not create fabricated transitions.
- [ ] **AC-06 — Resilience:** Parallel delegations, failed calls, errors, interrupted sessions, missing correlation identifiers, and partial event payloads are handled without crashing or inventing relationships.
- [ ] **AC-07 — Compact integrated UI:** The existing OpenCode v2.2.5 sidebar monitor presents hierarchy, task/delegation details, and recent activity in a compact, usable layout while preserving existing monitor behavior.
- [ ] **AC-08 — Read-only canonical state:** The monitor remains read-only with respect to Blueprint canonical files; no duplicate persistent state store, database, hosted service, or network dependency is introduced.
- [ ] **AC-09 — Regression and runtime verification:** Existing monitor tests remain passing; new automated tests cover the event mapping/correlation cases; OpenCode v2.2.5 load and live behavior are verified with reproducible evidence, or any environment limitation is explicitly documented without claiming a pass.

## Verification plan
1. Run the repository's documented validation/test commands after inspecting the current scripts and package configuration.
2. Add deterministic unit tests using representative OpenCode v2.2.5 event payloads, including incomplete and adversarial ordering cases.
3. Verify the canonical snapshot still renders correctly when no runtime events have been observed and when runtime event support is unavailable.
4. Exercise at least one real Orchestrator-to-agent delegation and return in OpenCode v2.2.5 if the installed configuration supports it; capture the observed event sequence and UI result.
5. Confirm that runtime session termination does not change canonical task status or imply review/approval.
6. Record exact commands, environment/version, outputs, test counts, and any checks not run in the completion evidence table.
7. Obtain an independent Manager Quality review before completion. Use the repository's official task lifecycle gate to transition to `done`.

## Risks and open questions
- OpenCode v2.2.5 may not expose enough event payload data to correlate every delegation edge or associate a runtime session with a TASK-NNN. The monitor must show partial/unknown information rather than infer it.
- Some workflow stages (review and user approval) may occur outside observable plugin events. These must remain sourced from canonical records or be labelled unobserved.
- If the discovery phase finds that the existing provider-neutral observability contract needs a material change, stop before changing the contract and present the proposed change and impact for Orchestrator/user approval.
- If runtime event correlation cannot reliably identify the task, keep the activity visible as uncorrelated rather than attach it to a guessed task.
- Do not split this into parallel implementation tasks; keep the baseline sequential.

## Blockers
None.

## Execution log
- 2026-11-06 — Task created as `ready` after confirming TASK-019 is `done`. No implementation has been started.

## Completion evidence

| Criterion | Criterion text | Evidence |
| --- | --- | --- |
| AC-01 | Verified runtime API | Pending |
| AC-02 | Honest hierarchy | Pending |
| AC-03 | Task and delegation detail | Pending |
| AC-04 | Lifecycle distinctions | Pending |
| AC-05 | Activity feed | Pending |
| AC-06 | Resilience | Pending |
| AC-07 | Compact integrated UI | Pending |
| AC-08 | Read-only canonical state | Pending |
| AC-09 | Regression and runtime verification | Pending |

## Next action
Start TASK-021 in OpenCode Build mode. First complete AC-01 technical discovery and present the event/correlation mapping and any material contract implications to the Orchestrator. Continue implementation only within the approved scope; stop and escalate if a material architecture decision or contract change is required.
