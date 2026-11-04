# TASK-004 — Define memory read/write protocol and startup context packet

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-002, SPEC-004
- Dependencies: TASK-003
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Specify deterministic startup loading and event-driven memory persistence.

## Scope
Define read order, context packet, record ownership, write triggers, and compaction rules.

## Out of scope
Do not add external memory infrastructure.

## Acceptance criteria
- [ ] Fresh-session startup protocol is deterministic.
- [ ] Context packet is concise and source-linked.
- [ ] Each durable fact has an owning record.
- [ ] Write triggers and non-write cases are explicit.

## Verification plan
Walk through a fresh session using only files and verify it can identify task, constraints, and next action.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
