---
description: Load canonical Blueprint state and produce the startup context packet
agent: orchestrator
---

Load this project's canonical Blueprint startup records in the required order, verify
their integrity, and report the startup context packet before planning work.

If the project is not initialized (no `.blueprint/` directory), stop and report that;
do not invent a memory layout. Read these records in order:

- `.blueprint/README.md`
- `.blueprint/manifest.json`
- `.blueprint/config/project.json`
- `.blueprint/config/agents.json`
- `.blueprint/memory/PROJECT_CONTEXT.md`
- `.blueprint/memory/CURRENT_STATE.md`
- `.blueprint/tasks/registry.json`
- The active task brief under `.blueprint/tasks/items/`
- The active task's linked specifications under `.blueprint/specs/`, in listed order

Read `.blueprint/memory/DECISIONS.md` for decisions referenced by the active task,
project constraints, or any conflict. If `CURRENT_STATE.md` names a handoff under
`.blueprint/handoffs/`, verify every claim against current files and Git before acting;
current files and Git win on disagreement.

Stop and report a blocking integrity issue rather than guessing if a required record
is missing, a version is unknown, multiple tasks are `in_progress`, task/registry
status disagrees, or a linked dependency/spec/brief is missing. Do not start a task
or write canonical records during startup.

Produce a concise 20-40 line context packet with:
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
- Sources: link the repository paths used.

$ARGUMENTS
