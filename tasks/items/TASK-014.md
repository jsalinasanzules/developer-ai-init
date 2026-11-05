# TASK-014 — Implement validation for schemas, task graph, references, and secrets

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Quality
- Specs: SPEC-009, SPEC-002, SPEC-005
- Dependencies: TASK-003, TASK-006, TASK-011, TASK-020
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Implement local validation for canonical records and adapter artifacts.

## Scope
Add schema validation, task graph checks, reference checks, and secret-pattern detection with redacted diagnostics.

## Out of scope
Do not print detected secret values or mutate project files during validation.

## Acceptance criteria
- [ ] Invalid schemas fail with actionable paths.
- [ ] Missing task/spec references and cycles are detected.
- [ ] Secret-like values are reported without disclosure.
- [ ] Validation works offline.

## Verification plan
Run unit/integration tests against positive and negative fixtures.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
