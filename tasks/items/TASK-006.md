# TASK-006 — Define task registry, status transitions, and handoff format

## Metadata
- Status: done
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
- [x] Task schema is complete.
- [x] Invalid transitions and dependency cycles are rejected.
- [x] Handoff template enables cold-start continuation.
- [x] Completion evidence maps to acceptance criteria.

## Verification plan
Test valid/invalid task records, dependency cycles, and handoff completeness.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-04: Re-read SPEC-005, the task registry schema, the task template, and the handoff template.
- 2026-11-04: Expanded `docs/architecture/task-lifecycle.md` with the task record schema, status vocabulary, full transition matrix, transition preconditions, dependency-graph rules, evidence mapping, handoff payload, and cold-start verification.
- 2026-11-04: Updated the task template with an acceptance-criterion-to-evidence table and retrofitted Risks/Blockers sections into all 18 task briefs.
- 2026-11-04: Updated the handoff template with acceptance evidence and a cold-start checklist.
- 2026-11-04: Ran structural and scenario checks: all task briefs contain required sections; handoff template contains all required headings; registry IDs are unique with no missing dependencies or cycles; synthetic cycle and missing-dependency graphs are rejected; an incomplete handoff is rejected.

## Completion evidence
- Task schema and required sections: §2 of [task-lifecycle.md](../../docs/architecture/task-lifecycle.md), `schemas/task-registry.schema.json`, and `tasks/TASK-TEMPLATE.md`.
- Transition matrix and terminal rules: §3–§5.
- Dependency rules and cycle rejection: §6.
- Evidence mapping: §7 and the task template table.
- Handoff payload and cold-start verification: §8–§9 and `handoffs/HANDOFF-TEMPLATE.md`.
- Observed checks:
  - `TASK BRIEF SECTION CHECK: PASS`
  - `HANDOFF SECTION CHECK: PASS`
  - `UNIQUE IDS: True`
  - `MISSING DEPS: []`
  - `CYCLES: []`
  - `SCENARIO cycle: [['TASK-001', 'TASK-002', 'TASK-001']] -> rejected`
  - `SCENARIO missing dependency: [('TASK-001', 'TASK-999')] -> rejected`
  - `SCENARIO incomplete handoff: rejected`
- Link and JSON checks run after the documentation changes.

## Next action
None. TASK-006 is done; TASK-007 and TASK-008 are eligible.
