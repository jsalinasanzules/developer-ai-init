# TASK-010 — Add OpenCode startup, task, and handoff workflows

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Engineering
- Specs: SPEC-002, SPEC-005, SPEC-007
- Dependencies: TASK-004, TASK-006, TASK-009
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Provide provider-native entry points for startup memory loading, task execution, memory consolidation, and handoff.

## Scope
Implement commands/skills/prompts supported by verified OpenCode capabilities.

## Out of scope
Do not create unsupported command mechanisms or bypass approval gates.

## Acceptance criteria
- [ ] Fresh session loads mandatory memory records.
- [ ] Agent identifies one eligible task and checks dependencies.
- [ ] Task completion updates records with evidence.
- [ ] Handoff can be produced and consumed.

## Verification plan
Perform cold-start test in a new OpenCode session using only repository files.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
