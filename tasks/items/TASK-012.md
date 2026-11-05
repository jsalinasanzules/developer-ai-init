# TASK-012 — Specify project discovery and interactive initialization

## Metadata
- Status: ready
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-008, SPEC-001
- Dependencies: TASK-001, TASK-002
- Created: 2026-11-04
- Updated: 2026-11-05

## Objective
Define how the blueprint discovers an existing/new project and gathers missing requirements before generating files.

## Scope
Specify discovery inventory, interview sequence, assumptions, confirmation summary, and approval points.

## Out of scope
Do not assume project stack or user requirements from repository contents alone.

## Acceptance criteria
- [ ] Existing and empty project flows are covered.
- [ ] Unknowns are explicit, not fabricated.
- [ ] User confirms summary before generation.
- [ ] Collision preview is part of the flow.

## Verification plan
Walk through representative greenfield and brownfield scenarios.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-05: Rechecked dependencies TASK-001 and TASK-002; both are `done`.
  Re-read SPEC-008 and SPEC-001.
- 2026-11-05: User approved the proposal and authorized transition to `ready`.
  No TASK-012 implementation began in this recovery.

## Completion evidence
Pending.

## Next action
Begin discovery-flow specification when TASK-012 is selected for execution;
transition to `in_progress` before starting work.
