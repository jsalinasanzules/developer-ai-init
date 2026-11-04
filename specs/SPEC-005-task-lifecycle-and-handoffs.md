# SPEC-005 — Task Lifecycle and Handoffs

## Requirements
- TASK-001: Tasks MUST have stable unique IDs.
- TASK-002: Tasks MUST declare status, priority, owner role, spec links, dependencies, scope, exclusions, acceptance criteria, and verification plan.
- TASK-003: Dependency cycles and references to missing tasks MUST be rejected by validation.
- TASK-004: Only dependency-satisfied `ready` tasks may start.
- TASK-005: Status transitions MUST be persisted.
- TASK-006: `done` MUST require evidence for every acceptance criterion.
- TASK-007: Blocked tasks MUST identify blocker, responsible role, and next action.
- TASK-008: Handoffs MUST describe repository state, completed work, evidence, unresolved decisions, and next action.
- TASK-009: Receiving sessions MUST verify handoff claims against current files and Git state.

## Status vocabulary
`proposed | ready | in_progress | blocked | in_review | done | cancelled`.

## Acceptance criteria
A task template, registry model, transition rules, and handoff template exist and are validated.
