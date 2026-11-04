# Memory Read/Write Protocol and Startup Context Packet

- Status: accepted design baseline for TASK-004
- Date: 2026-11-04
- Specs: SPEC-002, SPEC-004
- Related: SPEC-001, SPEC-005, `docs/architecture/memory-model.md`, `docs/architecture/target-project-layout.md`
- Applies to: initialized target projects under `.blueprint/`
- This repository's own development memory uses the same protocol with root `/memory`, `/tasks`, and `/specs` as the equivalent paths.

## 1. Purpose

Define a deterministic way for a fresh session to load project memory and a repeatable way to persist durable knowledge, so continuity does not depend on conversation history, a model, or a provider.

## 2. Principles

1. Repository files are authoritative; conversation history is ephemeral.
2. Startup reads a fixed minimum set in a fixed order.
3. The startup context packet is concise and source-linked; it does not copy whole files.
4. Every durable fact has exactly one owning record.
5. Writes are event-driven and reviewed; not every session event deserves a memory write.
6. Derived indexes and caches are optional and rebuildable.
7. Missing, contradictory, or unknown-version records are surfaced, not guessed.
8. No secrets, credentials, tokens, private keys, or unnecessary sensitive personal data are written.

## 3. Startup read protocol

### 3.1 Resolve the project root

1. Start from the current working directory.
2. Walk upward to the nearest ancestor containing `.blueprint/`.
3. Confirm it is the intended project root. If several nested roots exist, use the nearest and report the discovery.
4. If no `.blueprint/` exists, the project is not initialized. Stop and ask whether to initialize; do not invent a memory layout.

Special case: this blueprint repository uses root `/memory`, `/tasks`, `/specs`, `/sessions`, and `/handoffs` for its own development. Apply the same order with those path equivalents.

### 3.2 Read order

| Step | Read | Why it is required |
| --- | --- | --- |
| 1 | `.blueprint/README.md` | Startup entry point, project identity, navigation, startup order. |
| 2 | `.blueprint/manifest.json` | Installed blueprint/schema version and collision baseline. |
| 3 | `.blueprint/config/project.json` | Project facts, scope, constraints, initialization status, unknowns. |
| 4 | `.blueprint/config/agents.json` | Authority, role configuration, delegation mode, approval policy. |
| 5 | `.blueprint/memory/PROJECT_CONTEXT.md` | Durable narrative context and non-goals. |
| 6 | `.blueprint/memory/CURRENT_STATE.md` | Active task, blockers, pending approvals, next action. |
| 7 | `.blueprint/tasks/registry.json` | Authoritative task status and dependency graph. |
| 8 | Active task brief `.blueprint/tasks/items/TASK-<NNN>.md` | Scope, exclusions, acceptance criteria, verification plan, evidence. |
| 9 | Specifications linked by the active task, in the order listed | Normative requirements for the work. |

### 3.3 Conditional reads

Read only when the active task or answer requires them:

- `.blueprint/memory/DECISIONS.md` — read the decisions referenced by the task, project constraints, or conflict; search by ADR ID when the file is large.
- `.blueprint/memory/CONVENTIONS.md` — read before changing code, tests, documentation, branching, or review practice.
- `.blueprint/memory/ARCHITECTURE.md` — read when the task changes architecture, boundaries, data ownership, or integration.
- `.blueprint/handoffs/<latest>.md` — read when resuming from a handoff or when `CURRENT_STATE.md` names one; verify every claim against files and Git.
- `.blueprint/sessions/*.md` — read only the relevant recent session, not the whole history.
- `.blueprint/memory/metadata.json` — read when consolidating memory, checking ownership, or validating record freshness.
- `.blueprint/tasks/backlog.md` — read when planning phases or checking roadmap context; the registry remains authoritative.
- `.blueprint/derived/**` — optional accelerator only; never the sole source of a fact.

### 3.4 Active-task selection

After reading the registry:

1. If exactly one task is `in_progress`, it is the active task.
2. If more than one task is `in_progress`, stop and report a state conflict; do not choose silently.
3. If none is `in_progress`, select the highest-priority `ready` task whose dependencies are all `done`.
   - Priority order: `critical`, `high`, `medium`, `low`.
   - Tie-breaker: lowest task ID.
4. If no task is eligible, report that there is no eligible task and stop; do not fabricate work.
5. If the selected task brief is missing, stop; the registry and brief must be reconciled.
6. If the brief references a missing specification or dependency, stop; do not interpret around it.

### 3.5 Failure handling

| Condition | Required behavior |
| --- | --- |
| No `.blueprint/` | Not initialized; stop and ask. |
| Missing `manifest.json` in an existing `.blueprint/` | Treat as an unversioned/legacy installation; stop before writing and ask for reconciliation. |
| Unknown `blueprint_version` or `schema_version` | Stop writes; report the unknown version and request an upgrade or migration. |
| Missing required startup record | Blocking error; report the path. Do not reconstruct silently from chat. |
| Conflicting state between `CURRENT_STATE.md`, registry, and task brief | Stop and reconcile; registry wins for status, but never hide the mismatch. |
| Handoff contradicts current files or Git | Current files and Git win; record the discrepancy. |
| Read-only environment | Produce the context packet and stop before any write. |

## 4. Startup context packet

### 4.1 Required fields

The packet MUST contain:

- **Project:** name, slug, one-sentence purpose.
- **Stage:** current lifecycle stage.
- **Goal:** the goal of the active work, not the whole roadmap.
- **Constraints:** at most five binding constraints.
- **Active task:** ID, title, status, owner role, specs, dependencies.
- **Blockers:** current blockers or `None`.
- **Relevant decisions:** ADR IDs with one-line implications.
- **Pending approvals:** decisions or actions waiting on the user.
- **Next action:** one concrete step.
- **Sources:** repository paths used.

### 4.2 Size and quality rules

- Target 20–40 lines; do not exceed roughly 500 words.
- Link to source records instead of copying them.
- Prefer stable IDs (`TASK-*`, `SPEC-*`, `ADR-*`).
- Mark unknowns and assumptions explicitly.
- Do not include secrets or whole-file dumps.
- Do not present conversation history as a source of truth.
- If the active task is ambiguous, say so; do not invent a next action.

### 4.3 Template

```markdown
# Startup Context Packet

## Project
- Name / slug:
- Purpose:
- Stage:

## Goal
<one or two sentences>

## Constraints
- <max five>

## Active task
- ID / title:
- Status / owner role:
- Specs:
- Dependencies:

## State
- Blockers:
- Pending approvals:

## Relevant decisions
- ADR-XXX — <one-line implication>

## Next action
<one concrete step>

## Sources
- <paths read>
```

### 4.4 Worked example

This packet was produced from this repository's root development memory while TASK-004 was active. It demonstrates the same fields a target project would use with `.blueprint/` paths.

```markdown
# Startup Context Packet

## Project
- Name / slug: Developer AI Init / developer-ai-init
- Purpose: provider-agnostic blueprint for hierarchical AI coding agents and portable project memory
- Stage: core contracts; task graph in progress

## Goal
Define deterministic startup reads and event-driven memory persistence.

## Constraints
- Canonical memory is Git-native Markdown/JSON; no mandatory database.
- Orchestrator is the only user-facing role.
- Material decisions require user approval.
- Done requires observable evidence.
- OpenCode is the first adapter, not the core.

## Active task
- ID / title: TASK-004 / Define memory read/write protocol and startup context packet
- Status / owner role: in_progress / MANAGER: Architecture
- Specs: SPEC-002, SPEC-004
- Dependencies: TASK-003 (done)

## State
- Blockers: None.
- Pending approvals: initializer/validator implementation stack (deferred to TASK-012/TASK-013).

## Relevant decisions
- ADR-001 — Git-native Markdown/JSON is canonical.
- ADR-002 — No mandatory database.
- ADR-006 — OpenCode V2-native adapter baseline.
- ADR-007 — Depth-2 delegation is opt-in with sequential fallback.

## Next action
Complete the memory protocol document and verify the fresh-session walkthrough.

## Sources
- memory/PROJECT_CONTEXT.md
- memory/CURRENT_STATE.md
- tasks/registry.json
- tasks/items/TASK-004.md
- specs/SPEC-002-persistent-memory.md
- specs/SPEC-004-orchestration-and-conflicts.md
- memory/DECISIONS.md
```

## 5. Fact ownership map

Each durable fact has one owner. Other records link to it.

| Durable fact | Owning record |
| --- | --- |
| Project identity, purpose, users, goals, stack, constraints, unknowns | `config/project.json` for machine fields; `memory/PROJECT_CONTEXT.md` for narrative context |
| Roles, delegation, approval policy, adapter reference | `config/agents.json` |
| Current operational state, active task, blockers, next action | `memory/CURRENT_STATE.md` |
| Architecture and boundaries | `memory/ARCHITECTURE.md` |
| Material decision and rationale | `memory/DECISIONS.md` |
| Coding, testing, documentation, and operational conventions | `memory/CONVENTIONS.md` |
| Task scope, exclusions, acceptance criteria, verification, evidence | `tasks/items/TASK-<NNN>.md` |
| Task status, priority, owner, dependencies | `tasks/registry.json` |
| Roadmap view | `tasks/backlog.md` (projection; registry wins) |
| Normative requirements | `specs/SPEC-<NNN>-<slug>.md` |
| Session history | `sessions/YYYY-MM-DD-<slug>.md` |
| Continuation record | `handoffs/YYYY-MM-DD-<slug>.md` |
| Installed version and install hashes | `manifest.json` |
| Validation shapes | `schemas/*.schema.json` |
| Provider-native mapping | adapter documentation outside `.blueprint/` |

Duplication rule: if the same fact appears in two records, the owning record wins; correct or link the other record rather than letting both drift.

## 6. Write protocol

### 6.1 Write events

| Event | Owning record | Required synchronization | Approval |
| --- | --- | --- | --- |
| Project initialization confirmed | `config/project.json` | `PROJECT_CONTEXT.md`, `CURRENT_STATE.md`, manifest | User confirms the discovery summary |
| Durable project fact changes | `PROJECT_CONTEXT.md` or `project.json` | `metadata.json` | Material scope/ownership changes require user approval |
| Current state changes | `CURRENT_STATE.md` | `metadata.json` | No |
| Architecture changes | `ARCHITECTURE.md` | `DECISIONS.md`, `CURRENT_STATE.md` | Yes |
| Material decision approved | `DECISIONS.md` | `CURRENT_STATE.md`; affected specs/tasks | Yes |
| Convention changes | `CONVENTIONS.md` | `DECISIONS.md` if material | Material changes require approval |
| Task created | `registry.json` and task brief | `backlog.md`, `CURRENT_STATE.md` | Scope and acceptance criteria must be clear |
| Task status transition | `registry.json` and task brief | `backlog.md`, `CURRENT_STATE.md` | Follow the lifecycle; `done` needs evidence |
| Blocker discovered | `registry.json` blocker plus task brief | `CURRENT_STATE.md` | No, but the blocker must name an owner and next action |
| Verification evidence produced | Task brief completion evidence | Registry status if all criteria pass | No |
| Session summary | `sessions/YYYY-MM-DD-<slug>.md` | `metadata.json` | No |
| Handoff created | `handoffs/YYYY-MM-DD-<slug>.md` | `CURRENT_STATE.md` | No |
| Role or delegation change | `config/agents.json` | `CURRENT_STATE.md` | Material changes require approval |
| Blueprint upgrade | `manifest.json` | `CURRENT_STATE.md`, `DECISIONS.md` if material | Yes |
| Memory consolidation | `metadata.json` and owning records | `CURRENT_STATE.md` if operationally relevant | Orchestrator review |
| Specification change | Owning spec | Registry/task links if scope changes | Material changes require approval |
| Provider adapter generation | Provider-native files outside `.blueprint/` | Adapter manifest and `CURRENT_STATE.md` | Adapter collision policy applies |

### 6.2 Write sequence

1. **Identify the fact.** State it in one sentence and confirm it is durable rather than transient.
2. **Find the owner.** Use the ownership map; do not create a second copy.
3. **Read before writing.** Inspect the current record and Git status; preserve user changes.
4. **Check approval.** Material decisions, destructive actions, security/privacy changes, and scope changes require user approval.
5. **Write the owner.** Update the owning record with the fact, date, and evidence.
6. **Synchronize projections.** Update `CURRENT_STATE.md`, `backlog.md`, and metadata only where required.
7. **Verify.** Re-read the changed records, validate JSON/schema/links, and check that status and evidence agree.
8. **Record evidence.** Add the command output, review artifact, or link to the task brief.
9. **Commit.** Use a descriptive commit; never commit secrets.

### 6.3 Non-write cases

Do not write canonical memory for:

- transient reasoning, drafts, or exploratory prompts;
- a fact already recorded in its owning record;
- unapproved speculation, preferences, or proposed decisions;
- conversation history that is not durable project knowledge;
- secrets, credentials, tokens, private keys, or sensitive personal data;
- status changes without the required evidence;
- a no-op session with no meaningful discovery, decision, or transition;
- derived cache or index output (write it under `derived/`, never to canonical records).

### 6.4 Append-only and correction rules

- `DECISIONS.md` is append-only. Correct a decision by adding a superseding record and linking both.
- Session and handoff records are historical. Add a new correction rather than rewriting history.
- Task completion evidence may be extended, but not deleted to make a failed check look passed.
- If a record must be corrected, preserve the correction trail in `CURRENT_STATE.md` or a new decision when material.

## 7. Compaction rules

| Record | Compaction rule |
| --- | --- |
| `CURRENT_STATE.md` | Keep it under roughly 100 lines. Retain active work, blockers, pending approvals, recent completions, and next action. Move detail to task briefs, sessions, or handoffs. |
| `DECISIONS.md` | Never compact or delete. Use status and supersession links. |
| Task briefs | Keep the execution log concise; retain completion evidence and unresolved issues. Move long narratives to linked artifacts. |
| `sessions/*.md` | One page maximum. Summarize outcomes and links; do not paste full logs. |
| `handoffs/*.md` | Keep the latest actionable handoff concise. Older handoffs remain as history. |
| `metadata.json` | Keep pointers and timestamps only; never copy content. |
| `derived/**` | May be deleted and rebuilt at any time. |

When the model's context window fills, reload from repository files. A compaction summary is a convenience, not an authority.

## 8. Concurrency and consistency

- Read the current file and `git status` before writing.
- If another session changed the same record, reconcile semantically; do not use last-write-wins for decisions or task state.
- Conflicting task status, decisions, or ownership is a blocking error; stop and report.
- The Orchestrator consolidates specialist proposals before writing shared canonical records.
- Record a material reconciliation outcome in `DECISIONS.md`.
- TASK-007 defines the detailed consolidation and merge safeguards; this protocol establishes the baseline.

## 9. Fresh-session walkthrough (verification)

A session with no prior chat follows §3.1–§3.4 and produces the packet in §4.4. The walkthrough below uses this repository's root development memory as the equivalent of `.blueprint/`.

| Step | File read | Finding |
| --- | --- | --- |
| 1 | `memory/CURRENT_STATE.md` (equivalent to `.blueprint/README.md` plus current state) | Stage, active task, pending approvals, next action. |
| 2 | `memory/PROJECT_CONTEXT.md` | Purpose, non-goals, agreed direction, open questions. |
| 3 | `tasks/registry.json` | TASK-004 is active/ready; dependencies satisfied; no cycles. |
| 4 | `tasks/items/TASK-004.md` | Scope, acceptance criteria, verification plan. |
| 5 | `specs/SPEC-002-persistent-memory.md` and `SPEC-004-orchestration-and-conflicts.md` | Normative memory and startup requirements. |
| 6 | `memory/DECISIONS.md` | Canonical memory, no database, hierarchy, provider baseline, delegation. |
| 7 | `memory/CONVENTIONS.md` | Documentation, IDs, dates, evidence rules. |

Result: the session can identify the project, active task, constraints, relevant decisions, and next action using files alone. No conversation history or derived index is required.

## 10. Acceptance evidence for TASK-004

| Criterion | Evidence |
| --- | --- |
| Fresh-session startup protocol is deterministic | §3.1–§3.5: fixed order, active-task selection, failure handling. |
| Context packet is concise and source-linked | §4: required fields, size limits, template, worked example. |
| Each durable fact has an owning record | §5 ownership map. |
| Write triggers and non-write cases are explicit | §6.1, §6.3, §6.4. |
| Fresh-session walkthrough | §9. |
