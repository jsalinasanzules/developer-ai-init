# SPEC-002 — Persistent Memory Protocol

## Purpose
Specify portable, durable project memory independent of model/provider conversation history.

## Requirements
- MEM-001: Markdown/JSON files under `.blueprint/` MUST be canonical.
- MEM-002: Startup MUST load project context, current state, task registry, active task, and relevant specs/decisions.
- MEM-003: Durable facts MUST be written to their owning record, not duplicated indiscriminately.
- MEM-004: Approved material decisions MUST be recorded with context, options, choice, rationale, consequences, date, status, and supersession link where applicable.
- MEM-005: Task transitions and verification evidence MUST be persisted.
- MEM-006: Session summaries MUST be concise; handoffs MUST enable a fresh LLM to resume.
- MEM-007: Shared memory updates from specialists MUST be proposals reviewed by the Orchestrator/steward.
- MEM-008: Concurrent semantic edits MUST be reconciled; last-write-wins is prohibited for decisions and task state.
- MEM-009: Secrets and unnecessary sensitive data MUST NOT be stored.
- MEM-010: Optional indexes/caches MUST be rebuildable from canonical records.

## Startup packet
Produce a compact context packet containing project goal, constraints, current state, active task, dependencies, relevant decisions, and next action. Link to source records rather than copying entire files.

## Acceptance criteria
A new session with no access to previous chat can identify the project, active task, relevant constraints, and next action from repository files alone.
