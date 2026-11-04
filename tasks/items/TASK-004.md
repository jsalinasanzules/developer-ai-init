# TASK-004 — Define memory read/write protocol and startup context packet

## Metadata
- Status: done
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
- [x] Fresh-session startup protocol is deterministic.
- [x] Context packet is concise and source-linked.
- [x] Each durable fact has an owning record.
- [x] Write triggers and non-write cases are explicit.

## Verification plan
Walk through a fresh session using only files and verify it can identify task, constraints, and next action.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-04: Re-read SPEC-002, SPEC-004, the memory model, and the target-project layout.
- 2026-11-04: Defined the fixed startup read order, conditional reads, active-task selection, failure handling, context packet, ownership map, write events, non-write cases, compaction, and concurrency baseline in `docs/architecture/memory-protocol.md`.
- 2026-11-04: Added a fresh-session walkthrough and worked context packet using this repository's root memory as the equivalent of `.blueprint/`.
- 2026-11-04: Linked the protocol from the memory model, README, and AGENTS.md startup instructions.

## Completion evidence
- Deterministic startup protocol: §3.1–§3.5 of [memory-protocol.md](../../docs/architecture/memory-protocol.md).
- Context packet fields, size rules, template, and worked example: §4.
- Durable-fact ownership map: §5.
- Write triggers, non-write cases, and correction rules: §6.
- Compaction and concurrency rules: §7–§8.
- Fresh-session walkthrough: §9 (reads current state, context, registry, task brief, specs, decisions, conventions; identifies task, constraints, and next action).
- Link and JSON checks run after the documentation changes.

## Next action
None. TASK-004 is done; TASK-005 and TASK-006 are eligible.
