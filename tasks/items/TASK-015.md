# TASK-015 — Run end-to-end fresh-session continuity test

## Metadata
- Status: proposed
- Priority: critical
- Owner role: ORCHESTRATOR
- Specs: SPEC-002, SPEC-005, SPEC-007, SPEC-008, SPEC-009
- Dependencies: TASK-007, TASK-010, TASK-013, TASK-014
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Prove a new session/provider can continue project work from persisted files without prior conversation.

## Scope
Create repeatable scenario with initialized fixture, task in progress, decision, and handoff.

## Out of scope
Do not rely on hidden provider memory or manually injected prior chat context.

## Acceptance criteria
- [ ] New session reconstructs goal, constraints, active task, decisions, and next action.
- [ ] It validates dependencies and executes bounded work.
- [ ] It records evidence and updates memory.
- [ ] Handoff supports another provider/session.

## Verification plan
Execute documented cold-start test and preserve transcript/evidence with secrets removed.

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
