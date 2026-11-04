# TASK-005 — Define decision log, conflict detection, and approval workflow

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-004, SPEC-002
- Dependencies: TASK-004
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Formalize how the Orchestrator detects instruction conflicts and requests user decisions.

## Scope
Define conflict categories, severity, response format, approval record, expiry/reconsideration, and decision supersession.

## Out of scope
Do not resolve existing unresolved decisions on behalf of the user.

## Acceptance criteria
- [ ] Conflict sources and impacts are shown.
- [ ] Material decisions pause execution.
- [ ] Approval is explicit and attributable to user intent.
- [ ] Decisions are persisted with rationale and consequences.

## Verification plan
Test scenarios for conflicting specs, ambiguous user request, security-impacting change, and destructive action.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
