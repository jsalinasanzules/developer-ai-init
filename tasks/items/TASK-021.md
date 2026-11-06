# TASK-021 — Add live agent and delegation tracking to the OpenCode monitor

## Metadata
- Status: done
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
- [x] **AC-01 — Verified runtime API:** A discovery note documents the OpenCode v2.2.5 event/hooks used, their exact relevant payload fields, correlation limits, and evidence (API types/source references and tests or runtime observations). Unsupported assumptions are explicitly listed.
- [x] **AC-02 — Honest hierarchy:** The monitor displays the configured logical hierarchy separately from runtime agents/sessions actually observed; it never presents configured agents as active sessions without runtime evidence.
- [x] **AC-03 — Task and delegation detail:** The monitor displays canonical task ID/title/status and shows agent ownership, delegated work-item name, and delegation edges only when supported by canonical assignment data or correlated runtime evidence. Unknown/unobserved data is labelled clearly rather than inferred.
- [x] **AC-04 — Lifecycle distinctions:** Assignment/delegation, session execution, return/completion, review, and approval are represented as distinct states/events; session termination alone is not treated as task completion, review, or approval.
- [x] **AC-05 — Activity feed:** A compact chronological feed displays supported runtime events with stable ordering and useful task/session correlation; duplicate, missing, delayed, or out-of-order events do not create fabricated transitions.
- [x] **AC-06 — Resilience:** Parallel delegations, failed calls, errors, interrupted sessions, missing correlation identifiers, and partial event payloads are handled without crashing or inventing relationships.
- [x] **AC-07 — Compact integrated UI:** The existing OpenCode v2.2.5 sidebar monitor presents hierarchy, task/delegation details, and recent activity in a compact, usable layout while preserving existing monitor behavior.
- [x] **AC-08 — Read-only canonical state:** The monitor remains read-only with respect to Blueprint canonical files; no duplicate persistent state store, database, hosted service, or network dependency is introduced.
- [x] **AC-09 — Regression and runtime verification:** Existing monitor tests remain passing; new automated tests cover the event mapping/correlation cases; OpenCode v2.2.5 load and live behavior are verified with reproducible evidence, or any environment limitation is explicitly documented without claiming a pass.

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
- 2026-11-06 — Transitioned `ready` → `in_progress` via the task-status write event (memory protocol §6.1); no lifecycle gate exists for this transition (`scripts/task_lifecycle.py` gates only `in_review` → `done`). Registry, brief, backlog, and `CURRENT_STATE.md` synchronized. AC-01 discovery started.
- 2026-11-06 — AC-01 discovery completed in `docs/architecture/monitor-live-tracking-discovery-2026-11-06.md`; the user approved a bounded adapter-only implementation with no observability-contract change or persisted mirror.
- 2026-11-06 — Implemented `src/runtime-observations.ts`, `src/configured-hierarchy.ts`, and the sidebar integration; added `tests/monitor-runtime-observations.test.ts` (20/20 pass). `bun run scripts/verify-observability-snapshot.ts` → RESULT: PASS. One authorized Crouton Alpha v2.2.5 delegation check in an isolated fixture returned `blueprint fixture`, but it did **not** render the interactive TUI or prove live sidebar/event rendering.
- 2026-11-06 — Independent MANAGER: Quality review (two passes) found and rejected: out-of-order terminal handling, late create/idle status clobbering, missing evidence/approval handling, and unrelated bundled presentation heuristics. Code blockers 1–3 fixed and covered by regression tests (20/20).
- 2026-11-06 — User interactively confirmed in OpenCode v2.2.5 that the updated monitor title is visible, `/monitor` hides and shows it, and no errors appeared during startup/load. The user did **not** confirm live event/delegation data from the sidebar; no live-UI or runtime-data PASS is claimed beyond load/toggle.
- 2026-11-06 — User confirmed no extra live delegation/event-render run is required and accepted the documented limitation; TASK-021 advanced to `in_review`. The official completion gate remains uninvoked pending Manager Quality sign-off and explicit user approval.
- 2026-11-06 — The previously bundled `parseConformance`/`parseRegenerationSafety` presentation heuristics remain uncommitted and are explicitly excluded from TASK-021 evidence by user instruction.
- 2026-11-06 — User explicitly accepted the documented live limitation (load/`/monitor`/no-errors confirmed; live runtime/delegation rows NOT captured, no live PASS claimed) and authorized closing TASK-021. Recorded independent Manager Quality review `docs/reviews/task-021-manager-review-2.md` (Decision: APPROVED), completed the formal evidence/verification sections, excluded the unrelated `parseConformance`/`parseRegenerationSafety` presentation-heuristic bundle from the commit, and closed TASK-021 through the official lifecycle gate.

## Completion evidence
| Criterion | Criterion text | Evidence |
| --- | --- | --- |
| AC-01 | **AC-01 — Verified runtime API:** A discovery note documents the OpenCode v2.2.5 event/hooks used, their exact relevant payload fields, correlation limits, and evidence (API types/source references and tests or runtime observations). Unsupported assumptions are explicitly listed. | [Discovery note](../../docs/architecture/monitor-live-tracking-discovery-2026-11-06.md) documents v2.2.5 `data.listen`, session/tool/execution events, payload fields, correlation limits, unsupported assumptions (no TASK-NNN field, no review/approval event, lossy stream); event-mapping behaviour exercised by [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_child_session_linked_only_with_parent_id`). Evidence: PASS with documented limitation (live rows not captured). |
| AC-02 | **AC-02 — Honest hierarchy:** The monitor displays the configured logical hierarchy separately from runtime agents/sessions actually observed; it never presents configured agents as active sessions without runtime evidence. | `configured-hierarchy.ts` reads `.blueprint/config/agents.json` or reports `unavailable` without inventing roles; TUI keeps configured hierarchy separate from observed-runtime counts; [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_configured_hierarchy_from_agents_file`, `test_configured_hierarchy_missing_is_unavailable`). Evidence: PASS. |
| AC-03 | **AC-03 — Task and delegation detail:** The monitor displays canonical task ID/title/status and shows agent ownership, delegated work-item name, and delegation edges only when supported by canonical assignment data or correlated runtime evidence. Unknown/unobserved data is labelled clearly rather than inferred. | Only canonical task ID/title/status from registry; delegation edges require parent subagent invocation plus correlated child with `parentID`; unobserved parents remain labelled `parent unobserved` and edges `unresolved`; no TASK-NNN association invented; [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_delegation_links_require_invocation_evidence`, `test_unobserved_parent_reported`). Evidence: PASS. |
| AC-04 | **AC-04 — Lifecycle distinctions:** Assignment/delegation, session execution, return/completion, review, and approval are represented as distinct states/events; session termination alone is not treated as task completion, review, or approval. | Assignment/delegation, execution attempts, terminal outcomes, and idle are distinct states; session end never implies review/approval (`review: unobserved`, `approval: unobserved`); [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_session_end_does_not_imply_approval`). Evidence: PASS. |
| AC-05 | **AC-05 — Activity feed:** A compact chronological feed displays supported runtime events with stable ordering and useful task/session correlation; duplicate, missing, delayed, or out-of-order events do not create fabricated transitions. | Stable `(at, id)` ordering, duplicate event-ID suppression, 100-item in-memory cap, compact last-5 display; [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_activity_feed_stable_ordering_and_cap`). Live feed rows not observed — documented limitation, not claimed. Evidence: PASS. |
| AC-06 | **AC-06 — Resilience:** Parallel delegations, failed calls, errors, interrupted sessions, missing correlation identifiers, and partial event payloads are handled without crashing or inventing relationships. | Parallel ambiguous links, malformed/unparseable payloads, missing IDs, failure/interruption, and disconnect-stays-incomplete handled without crashes or invented edges; [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_parallel_and_malformed_payloads_do_not_crash`, `test_disconnect_stays_incomplete`). Evidence: PASS. |
| AC-07 | **AC-07 — Compact integrated UI:** The existing OpenCode v2.2.5 sidebar monitor presents hierarchy, task/delegation details, and recent activity in a compact, usable layout while preserving existing monitor behavior. | Single existing `sidebar.content` slot preserved with compact layout; user confirmed `Blueprint Monitor` visible, `/monitor` hide/show, no startup/load errors in OpenCode v2.2.5; hierarchy/delegation/activity sections present with honest labels checked by [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_sidebar_renders_honest_runtime_labels`). Live delegation rows were NOT rendered/observed — accepted documented limitation, NOT claimed as verified. Evidence: PASS under accepted limitation. |
| AC-08 | **AC-08 — Read-only canonical state:** The monitor remains read-only with respect to Blueprint canonical files; no duplicate persistent state store, database, hosted service, or network dependency is introduced. | Runtime layer is in-memory only with no canonical writes, database, service, or network; snapshot verifier `A: no writes to canonical root` PASS; [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_runtime_state_never_writes_canonical_records`). Evidence: PASS. |
| AC-09 | **AC-09 — Regression and runtime verification:** Existing monitor tests remain passing; new automated tests cover the event mapping/correlation cases; OpenCode v2.2.5 load and live behavior are verified with reproducible evidence, or any environment limitation is explicitly documented without claiming a pass. | 31 deterministic tests pass (20+11); snapshot verifier RESULT: PASS; OpenCode v2.2.5 load/toggle/no-errors confirmed live; live event-subscription/delegation rows explicitly documented as unverified without claiming a pass, as this criterion permits; [named tests](../../tests/monitor-runtime-observations-evidence.test.ts) (`test_delegation_links_require_invocation_evidence`) and [verification report](../../docs/reviews/task-021-verification.md). Evidence: PASS via documented-limitation clause. |

## Manager review

`docs/reviews/task-021-manager-review-2.md`

Independent Manager Quality review (2nd pass) approving completion under the user's explicit documented-limitation decision for live runtime/delegation rows (AC-09 limitation clause). Prior REJECTED review: `docs/reviews/task-021-manager-review.md`.

## Verification results

| Check | Command | Result | Report |
| --- | --- | --- | --- |
| Deterministic runtime tests | `bun test tests/monitor-runtime-observations.test.ts` | PASS | [Report](../../docs/reviews/task-021-verification.md) |
| Named evidence tests | `bun test tests/monitor-runtime-observations-evidence.test.ts` | PASS | [Report](../../docs/reviews/task-021-verification.md) |
| Observability snapshot | `bun run scripts/verify-observability-snapshot.ts` | PASS | [Report](../../docs/reviews/task-021-verification.md) |

Live TUI check (OpenCode 2.2.5): plugin load, `Blueprint Monitor` visibility, `/monitor` hide/show, no startup/load errors — user-confirmed. Live runtime/delegation rows were NOT captured and no live PASS is claimed; see [live evidence](../../docs/reviews/task-021-live-evidence/README.md).

## Next action
TASK-021 completed via the official lifecycle gate: independent Manager Quality review docs/reviews/task-021-manager-review-2.md (Decision: APPROVED), 31 deterministic tests pass, snapshot verifier RESULT: PASS, OpenCode 2.2.5 load/toggle user-confirmed, live runtime/delegation rows documented as unverified under the accepted limitation. Do not start TASK-016/017/018 without user direction.

