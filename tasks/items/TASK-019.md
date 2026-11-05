# TASK-019 — Define provider-neutral observability contract and OpenCode monitor

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-006, SPEC-007
- Dependencies: TASK-002, TASK-006, TASK-008
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Define a provider-neutral observability contract for Blueprint execution and specify the first provider-specific presentation, `developer-ai-init-monitor`, as an OpenCode TUI sidebar plugin.

## Context
ADR-008 establishes that observability semantics and canonical state belong to the Blueprint core, while provider-specific monitor UIs belong to adapters. The monitor source is owned/versioned in this Blueprint repository, installed by the initializer into generated projects, and reads canonical state from the generated project's `.blueprint/` directory. The monitor is optional and must never become a second source of truth.

## Scope
- Define the core observability data model for task state, active execution, role/agent assignments, progress evidence, blockers, approval requests, handoffs, and update timestamps.
- Define data ownership, event/update semantics, freshness indicators, and consistency expectations.
- Define provider-neutral interfaces/contracts consumed by provider adapters.
- Specify the OpenCode monitor's responsibilities, plugin packaging/discovery, TUI sidebar integration, and supported-version compatibility checks.
- Define degraded/manual behavior when live OpenCode events or sidebar capabilities are unavailable.
- Define installation, configuration, versioning, collision detection, and safe upgrade expectations.
- Establish a minimal compatibility spike and verification plan for OpenCode 2.2.5 before committing to implementation details.

## Out of scope
- Implementing the full OpenCode plugin UI.
- Modifying OpenCode itself.
- Making a hosted monitoring service, database, or network connection mandatory.
- Duplicating canonical task, approval, agent, or handoff state inside the plugin.
- Implementing Claude Code or Cursor monitor UIs.

## Acceptance criteria
- [ ] A provider-neutral observability contract and data ownership model are documented.
- [ ] Required fields and lifecycle/update semantics are defined for tasks, agents, blockers, approvals, and handoffs.
- [ ] OpenCode TUI plugin architecture and sidebar integration are verified against official documentation and a minimal compatibility spike for v2.2.5.
- [ ] Installation and upgrade behavior is optional, reproducible, versioned, and non-destructive.
- [ ] A degraded mode displays last persisted state and its freshness when live updates are unavailable.
- [ ] Core workflows remain fully usable with the monitor disabled or unavailable.

## Verification plan
- Review the contract against existing task, memory, decision, and handoff schemas.
- Validate all referenced fields against the current schemas or propose explicit schema changes.
- Run a minimal OpenCode 2.2.5 plugin spike to verify discovery, TUI entrypoint, sidebar slot, and update behavior.
- Test that the monitor reads canonical files and does not mutate authoritative state.
- Review safe installation behavior against existing `.opencode/` user configuration.

## Risks and open questions
- OpenCode plugin/TUI APIs may change between releases; pin and document the verified compatibility range.
- The exact split between persisted snapshots and live provider events must be explicit.
- Avoid coupling the core schema to OpenCode-specific session or event identifiers.

## Blockers
None.

## Execution log
- 2026-11-04: Created after user approval of ADR-008.

## Completion evidence

| Criterion | Evidence |
| --- | --- |
| Provider-neutral contract | Pending |
| OpenCode v2.2.5 compatibility spike | Pending |
| Optional, safe installation and degraded mode | Pending |

## Next action
Define the provider-neutral observability model and its adapter-facing contract.
