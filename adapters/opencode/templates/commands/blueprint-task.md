---
description: Execute a Blueprint task under the delegation and evidence protocol
agent: orchestrator
---

Execute Blueprint task $ARGUMENTS under the project's task lifecycle.

1. Read the task brief `.blueprint/tasks/items/<TASK-ID>.md`, its registry entry, and
   linked specs from `.blueprint/specs/`. Confirm the task is `ready` (or
   `in_progress` for continuation), the brief and registry agree, no other task is
   `in_progress`, and every dependency is `done` with checked criteria and completion
   evidence in its matching brief. Stop on any mismatch and report.
2. Announce the plan: objective, allowed scope, forbidden changes, acceptance criteria,
   and how work will be delegated (Managers for review, Specialist for scoped
   execution; with subagent depth 1, pass the Specialist return back through a
   Manager review before proceeding).
3. Before execution, transition `ready` to `in_progress` in the registry and task brief;
   update `.blueprint/memory/CURRENT_STATE.md` and the backlog projection. Preserve
   task status and evidence if continuing an `in_progress` task.
4. Delegate with the full payload (objective, context, scope, exclusions, dependencies,
   constraints, artifacts, acceptance criteria, return format, escalation). Use the
   documented sequential fallback when nested delegation is unavailable.
5. Review returned evidence before accepting: confirm commands were run and outputs
   observed; reject assertions. Specialists and Managers never write canonical
   records; their durable findings are proposals you review.
6. Apply accepted changes to the owning canonical record, synchronize projections
   (`CURRENT_STATE.md`, registry, backlog), and update the task brief's execution log
   and completion evidence. Map every acceptance criterion to an observed result.
7. Move through valid lifecycle transitions (`ready → in_progress → in_review → done`).
   Mark `in_review` after implementation; set `done` only after every criterion is
   checked, its evidence is recorded, and review is complete. Never infer completion
   from a handoff or an assertion. Record blockers with reason, responsible role, and
   next action.
8. If a material decision is required (architecture, security, privacy, scope,
   ownership, compatibility, destructive action), stop and ask the user one explicit
   question with sources, impacts, and options. Do not write the contested change.
9. Commit with a descriptive message when authorized by the user or project workflow.
   Never commit secrets.

Finish by summarizing: scope completed, files changed, verification evidence, and next
action.
