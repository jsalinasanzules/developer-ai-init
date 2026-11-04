# Task Lifecycle, Registry, and Handoffs

- Status: accepted design baseline for TASK-006
- Date: 2026-11-04
- Spec: SPEC-005
- Related: SPEC-002, SPEC-004, `schemas/task-registry.schema.json`

## 1. Purpose

Define the task record, allowed status transitions, dependency-graph validation, evidence-based completion, and the handoff payload required for a fresh session to continue safely.

## 2. Task record

A task has two synchronized representations:

1. **Registry entry** in `tasks/registry.json` — machine-readable status, priority, owner role, spec links, dependencies, blocker, next action.
2. **Task brief** in `tasks/items/TASK-<NNN>.md` — objective, context, scope, exclusions, acceptance criteria, verification plan, risks, blocker, execution log, and completion evidence.

The JSON shape is defined by `schemas/task-registry.schema.json`. A task brief MUST contain these sections:

- Metadata: status, priority, owner role, specs, dependencies, created/updated dates.
- Objective.
- Context.
- Scope.
- Out of scope.
- Acceptance criteria (checkboxes).
- Verification plan.
- Risks and open questions.
- Blockers.
- Execution log.
- Completion evidence mapped to acceptance criteria.
- Next action.

Rules:

- IDs are stable, unique, zero-padded (`TASK-001`), and never reused.
- Registry and brief MUST agree on ID, title, status, specs, owner role, and dependencies. A mismatch is a blocking integrity error.
- The registry is authoritative for status; the brief is authoritative for scope, acceptance criteria, and evidence.
- `backlog.md` is a human-readable projection; the registry wins on conflict.
- One task is active by default. Multiple `in_progress` tasks are a state conflict unless a future approved parallel-execution extension explicitly records the group. The baseline protocol is sequential.
- A task may be cancelled with a rationale; IDs are not recycled.

## 3. Status vocabulary

| Status | Meaning |
| --- | --- |
| `proposed` | Captured but not ready to start; scope, dependencies, or acceptance criteria may be incomplete. |
| `ready` | Dependencies are done and scope/acceptance criteria are clear enough to start. |
| `in_progress` | Actively being executed. |
| `blocked` | Cannot proceed; blocker, responsible role, and next action are recorded. |
| `in_review` | Implementation is complete but verification, evidence review, or approval is pending. |
| `done` | Every acceptance criterion has recorded evidence and review is complete. Terminal. |
| `cancelled` | Intentionally stopped with a recorded rationale. Terminal. |

## 4. Transition matrix

`✓` allowed; `—` rejected. Same-status writes are no-ops, not transitions.

| From \ To | proposed | ready | in_progress | blocked | in_review | done | cancelled |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **proposed** | — | ✓ | — | — | — | — | ✓ |
| **ready** | — | — | ✓ | ✓ | — | — | ✓ |
| **in_progress** | — | — | — | ✓ | ✓ | — | ✓ |
| **blocked** | — | ✓ | ✓ | — | — | — | ✓ |
| **in_review** | — | — | ✓ | ✓ | — | ✓ | ✓ |
| **done** | — | — | — | — | — | — | — |
| **cancelled** | — | — | — | — | — | — | — |

Terminal-state rule: `done` and `cancelled` do not transition. If new evidence invalidates a `done` task, create a follow-up task that references it; do not rewrite completion history. If a cancelled task is needed again, create a new task.

## 5. Transition preconditions

### 5.1 proposed → ready

- Every dependency exists and is `done` with evidence.
- Scope, exclusions, acceptance criteria, and verification plan are present.
- Linked specifications exist and do not conflict with the task.
- Owner role is valid.

### 5.2 ready → in_progress

- Dependencies remain `done`.
- No other task is `in_progress` in the baseline sequential mode.
- The active task brief and registry agree.
- Required approvals for the task's scope are recorded.

### 5.3 any active status → blocked

- `blocked.reason` names the blocker.
- `blocked.responsible_role` names who must resolve it.
- `blocked.next_action` is concrete.
- `CURRENT_STATE.md` reflects the blocker.
- A task blocked by an unmet dependency or unresolved decision may not be marked `ready` or `in_progress` until the blocker is resolved.

### 5.4 blocked → ready or in_progress

- The blocker is resolved and the resolution evidence is recorded.
- Dependencies are still satisfied.
- If the blocker changed scope or architecture, the task and relevant decisions are updated.

### 5.5 in_progress → in_review

- Implementation is complete for the approved scope.
- Every acceptance criterion has been addressed.
- Evidence is collected but may still need review.
- Any incomplete criterion is explicitly marked.

### 5.6 in_review → done

- Every acceptance criterion is checked.
- Each criterion maps to inspectable evidence in the task brief.
- The Orchestrator has reviewed the evidence against the spec.
- No blocker or pending material approval remains.
- The registry and brief both record `done`.

### 5.7 in_review → in_progress

- Review found a gap, regression, or missing evidence.
- Record the reason and a new next action.
- Do not delete prior evidence.

### 5.8 any non-terminal status → cancelled

- Rationale is recorded.
- User approval is required when cancellation changes approved scope or material direction.
- Downstream tasks are reviewed for dependency impact.

## 6. Dependency graph

The dependency graph is a directed acyclic graph where a task points to the tasks that must finish first.

Validation rules:

- **D-01:** Task IDs are unique.
- **D-02:** Every dependency ID resolves to an existing task.
- **D-03:** No task depends on itself.
- **D-04:** No cycles exist. Reject a cycle and name every task in it.
- **D-05:** A dependency is satisfied only by `done` with evidence. `cancelled` is not satisfied; it requires a replacement or an approved scope change.
- **D-06:** A `ready` or `in_progress` task has all dependencies `done`.
- **D-07:** Dependencies are ordered deterministically for scheduling: priority (`critical`, `high`, `medium`, `low`), then task ID.
- **D-08:** Removing or changing a dependency requires a task-scope review and synchronization of registry, brief, and backlog.
- **D-09:** Cross-task cycles introduced by splitting or merging tasks are rejected.

Example rejected cycle: `TASK-010 → TASK-011 → TASK-010`. The validator must reject the registry and report both edges; neither task may start.

## 7. Acceptance criteria and completion evidence

### 7.1 Criterion format

Each criterion is an observable checkbox:

```markdown
- [ ] The command `./scripts/validate.sh` exits 0.
```

Avoid unobservable criteria such as "works well" or "is good".

### 7.2 Evidence mapping

The task brief's completion evidence MUST map every criterion to evidence:

```markdown
## Completion evidence

| Criterion | Evidence |
| --- | --- |
| 1. <criterion> | `./scripts/validate.sh` exited 0 on 2026-11-04; output recorded below. |
| 2. <criterion> | `docs/architecture/example.md` §4 documents the required behavior. |
| 3. <criterion> | Review artifact `docs/reviews/example-review.md` confirms the scenario. |
```

Acceptable evidence:

- exact command and observed output;
- a file path and section that demonstrates the result;
- a test result with date and environment;
- a review artifact;
- a verified behavior with reproduction steps;
- an external source with URL and access date, when the criterion is about provider behavior.

Unacceptable evidence:

- "Implemented" without an artifact;
- a command that was not run;
- a model's assertion that something works;
- a handoff claim not verified against files;
- a link to a missing file;
- evidence for a different criterion.

### 7.3 Completion rule

`done` requires all criteria checked and evidenced. If any criterion is unverified, use `in_review` or `blocked`. If evidence becomes stale because code changed after verification, re-run the check before claiming completion.

## 8. Handoff payload

A handoff is a continuation record, not a substitute for canonical memory. It MUST include:

1. **Repository state:** branch, commit (or explicit uncommitted state), working-tree status.
2. **Active task:** ID, title, status, specs, dependencies.
3. **Completed work:** verified outcomes only.
4. **Files changed:** paths and purpose.
5. **Verification evidence:** commands/checks and observed results; explicitly list checks not run.
6. **Acceptance criteria evidence:** table mapping each criterion to evidence.
7. **Decisions and approvals:** ADR IDs, approved scope, pending approvals.
8. **Risks and blockers:** impact, responsible role, next action.
9. **Memory updates:** records changed.
10. **Exact next action:** one concrete step.
11. **Startup reminder:** files to read and claims to verify.

The template is `handoffs/HANDOFF-TEMPLATE.md` in the blueprint source and `.blueprint/handoffs/HANDOFF-TEMPLATE.md` in a target project.

## 9. Receiving-agent verification (cold start)

A receiving session MUST:

1. Read `AGENTS.md`, the startup records, the active task brief, and relevant specs.
2. Produce the startup context packet from `docs/architecture/memory-protocol.md`.
3. Inspect Git state and verify the handoff's branch/commit/working-tree claims.
4. Compare the handoff's active task, status, files, and evidence with the current repository.
5. Run the stated verification commands where practical.
6. Treat current files and Git as authoritative when the handoff disagrees; record the discrepancy.
7. Confirm the next action is still eligible and dependencies are satisfied.
8. Never mark work `done` based only on a handoff claim.

## 10. Validation scenarios

These are design tests for TASK-014 implementation; until then they are review scenarios.

| Scenario | Expected result |
| --- | --- |
| Valid registry with acyclic dependencies and matching briefs | Accepted. |
| `ready` task with an unfinished dependency | Rejected with the dependency named. |
| `TASK-002` depends on `TASK-001`, and `TASK-001` depends on `TASK-002` | Rejected as a cycle naming both edges. |
| Dependency references `TASK-999` | Rejected as missing. |
| `blocked` status without `blocked` details | Rejected by schema and semantic validation. |
| `done` without evidence for one criterion | Rejected; status must be `in_review` or `blocked`. |
| `ready → done` transition | Rejected; must pass through `in_progress`/`in_review`. |
| Handoff without commit or verification evidence | Rejected as incomplete. |
| Handoff with all required sections and a cold-start checklist | Accepted; receiving agent verifies claims. |
| Registry and task brief disagree on status | Blocking integrity error; reconcile before starting. |

## 11. Acceptance evidence for TASK-006

| Criterion | Evidence |
| --- | --- |
| Task schema is complete | §2, the JSON schema, and the updated task template. |
| Invalid transitions and dependency cycles are rejected | §4, §5, §6, and §10. |
| Handoff template enables cold-start continuation | §8, §9, and the updated handoff template. |
| Completion evidence maps to acceptance criteria | §7 and the updated evidence table. |
