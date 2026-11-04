# TASK-006 — Define task registry, status transitions, and handoff format

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Delivery
- Specs: SPEC-005
- Dependencies: TASK-003
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Specify task record schema, dependency graph semantics, status transition validation, and handoff payload.

## Scope
Define required task fields, transition matrix, dependency checks, and receiving-agent verification.

## Out of scope
Do not mark tasks done without evidence.

## Acceptance criteria
- [ ] Task schema is complete.
- [ ] Invalid transitions and dependency cycles are rejected.
- [ ] Handoff template enables cold-start continuation.
- [ ] Completion evidence maps to acceptance criteria.

## Verification plan
Test valid/invalid task records, dependency cycles, and handoff completeness.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
