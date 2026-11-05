---
description: Load canonical Blueprint state and produce the startup context packet
agent: orchestrator
---

Load this project's Blueprint startup records and report the startup context packet.

If the project is not initialized (no `.blueprint/` directory), stop and report that;
do not invent a memory layout. If a handoff under `.blueprint/handoffs/` is named in
`.blueprint/memory/CURRENT_STATE.md`, verify every handoff claim against current files
and Git before acting; current files and Git win on disagreement.

Produce a concise context packet (20-40 lines) with:
- Project: name/slug from `.blueprint/config/project.json`, purpose, stage.
- Goal: the active task's goal, not the whole roadmap.
- Constraints: at most five binding constraints.
- Active task: ID/title/status/owner role/specs/dependencies
  (select per `.blueprint/tasks/registry.json`: a task is `in_progress` if set;
  otherwise the highest-priority `ready` task whose dependencies are all `done`,
  ties broken by lowest ID). Report a conflict if multiple tasks are `in_progress`.
- Blockers and pending approvals from `.blueprint/memory/CURRENT_STATE.md`.
- Relevant decisions: ADR IDs from `.blueprint/memory/DECISIONS.md` with one line each.
- Next action: one concrete step, then wait for the user before starting work.

$ARGUMENTS
