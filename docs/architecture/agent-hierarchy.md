# Agent Hierarchy, Role Contracts, and Delegation

- Status: accepted design baseline for TASK-008
- Date: 2026-11-04
- Specs: SPEC-003, SPEC-004
- Related: SPEC-002, SPEC-005, `docs/architecture/decision-and-approval-protocol.md`, `docs/architecture/memory-consolidation.md`, `docs/architecture/task-lifecycle.md`
- Reusable prompt templates: [`prompts/`](../../prompts/README.md)

## 1. Purpose

Define the logical roles in `USER → ORCHESTRATOR → MANAGERS → SPECIALISTS`, the authority each role holds, the payloads passed down and up, the review gates, the escalation routes, and how the same contracts work when a provider supports only sequential execution.

Roles are logical responsibilities, not a requirement to run separate processes. One model may play several roles in sequence, provided the authority boundaries and artifacts below are preserved.

## 2. Invariants (testable boundaries)

These are the rules a review or conformance test can check directly. Each has a stable ID.

| ID | Invariant | How to test |
| --- | --- | --- |
| B-01 | Only the Orchestrator communicates with the user. | Inspect transcripts/outputs: no Manager or Specialist asks the user a question or presents an approval request. |
| B-02 | Every delegation contains objective, context, scope, exclusions, dependencies, artifacts, acceptance criteria, and return format. | Validate each delegation against §4. Missing field = invalid delegation. |
| B-03 | Specialists do not write shared canonical records. | Check that canonical files changed only through the Orchestrator/steward proposal workflow. |
| B-04 | Specialists do not approve material decisions. | Check that every material decision cites a `USER` approval recorded per the decision protocol. |
| B-05 | Managers review specialist output before forwarding. | Each manager report references the reviewed specialist report and states accept/reject/revise. |
| B-06 | The Orchestrator validates results against specs and acceptance criteria. | Completion evidence maps every criterion to an inspectable artifact. |
| B-07 | Material decisions pause execution until explicit user approval. | No contested change is written before an approval record exists. |
| B-08 | Sequential fallback produces the same artifacts as delegated execution. | Run the §11 sample sequentially; confirm delegation, return, review, and evidence records exist. |
| B-09 | No role claims a provider capability that is not present. | Adapter docs distinguish native delegation, sequential fallback, and unsupported behavior. |
| B-10 | Every role output is evidence-backed and source-linked. | Reports cite paths, commands, and observed results, not assertions. |

## 3. Role contracts

A role contract has: purpose, authority, required inputs, obligations, prohibitions, output contract, and done criteria.

### 3.1 USER

- **Purpose:** own product intent, priorities, and approval of material decisions.
- **Authority:** may change goals, scope, priorities; may approve or reject material options; may edit any file but should route durable changes through the Orchestrator.
- **Inputs:** decision/approval packets from the Orchestrator.
- **Obligations:** answer the one question asked, or explicitly defer; state constraints that affect the choice.
- **Prohibitions:** none imposed by the blueprint; the user remains the authority.
- **Output:** an explicit decision, rejection, change request, or deferral.
- **Done:** the Orchestrator has recorded the outcome with attribution per the decision protocol.

### 3.2 ORCHESTRATOR

- **Purpose:** be the user's sole counterpart and retain accountability for all delegated work.
- **Authority:** classify requests, plan work, select and delegate to Managers, validate results, request approvals, consolidate approved memory, declare task transitions within the lifecycle.
- **Required inputs:** the startup context packet, active task brief, linked specs, relevant decisions, current Git state.
- **Obligations:**
  - load persistent context before planning (ORCH-001);
  - classify the request: project initialization, new task, continuation, change request, question, or incident (ORCH-002);
  - detect conflicts and present sources, impacts, options, and one approval question (ORCH-003, ORCH-004);
  - delegate with the full payload in §4;
  - validate delegated results against specs and acceptance criteria (ORCH-007);
  - consolidate approved durable knowledge and record provenance (ORCH-008);
  - keep `CURRENT_STATE.md`, the registry, and the task brief synchronized.
- **Prohibitions:**
  - must not delegate away accountability or accept a specialist assertion as evidence;
  - must not approve a material decision on the user's behalf;
  - must not write canonical memory from an unreviewed proposal;
  - must not bypass the task lifecycle or evidence rules.
- **Output contract:** to the user, a concise status/decision/approval request; to Managers, a delegation payload; to canonical memory, reviewed changes with provenance.
- **Done:** the user's request is satisfied within approved scope, results are evidenced, and memory/task state is synchronized.

### 3.3 MANAGER

- **Purpose:** coordinate a bounded domain and turn approved scope into reviewed specialist work.
- **Authority:** decompose approved scope, assign bounded work, decide ordinary domain-level implementation details within approved constraints, accept/reject/revise specialist output, propose spec/task/architecture changes.
- **Required inputs:** a valid delegation from the Orchestrator, relevant specs/decisions, current repository state.
- **Obligations:**
  - confirm the delegation is complete and dependencies are satisfied;
  - decompose into specialist-sized units with explicit boundaries;
  - review each specialist return against its acceptance criteria and evidence;
  - resolve ordinary implementation choices and record them;
  - aggregate results into one report with conflicts and risks surfaced;
  - forward material conflicts rather than deciding them.
- **Prohibitions:**
  - must not ask the user anything directly;
  - must not approve material product/architecture/security/scope decisions;
  - must not write shared canonical records directly (proposals only);
  - must not accept a specialist report without checking evidence;
  - must not expand scope beyond the Orchestrator's delegation.
- **Output contract:** a manager report per §5, plus proposals per §6.
- **Done:** every assigned unit has reviewed evidence, conflicts are escalated, and the report is ready for Orchestrator validation.

### 3.4 SPECIALIST

- **Purpose:** execute one bounded unit of work and return verifiable evidence.
- **Authority:** inspect relevant files, run approved local checks, make changes inside the assigned scope, propose memory updates.
- **Required inputs:** a delegation containing objective, context references, allowed scope, forbidden changes, dependencies, expected artifacts, acceptance criteria, and return format.
- **Obligations:**
  - restate the objective and boundaries before acting;
  - inspect current state rather than assuming it;
  - keep changes inside scope;
  - run the specified verification and report exact commands and outcomes;
  - report risks, open questions, and proposed memory updates with evidence.
- **Prohibitions:**
  - must not redefine scope, acceptance criteria, or dependencies;
  - must not approve material decisions or ask the user directly;
  - must not overwrite shared canonical records;
  - must not claim a command or check succeeded unless it was run and observed;
  - must not expand into another domain without escalation.
- **Output contract:** a specialist return per §5.
- **Done:** the assigned acceptance criteria are addressed with evidence, or the unit is returned as blocked with a concrete next action.

## 4. Delegation payload

Every downward delegation uses this structure. Fields are mandatory unless marked optional.

```markdown
## Delegation — <delegation-id>
- From: ORCHESTRATOR | MANAGER: <domain>
- To: MANAGER: <domain> | SPECIALIST: <role>
- Task: TASK-NNN
- Objective: <one sentence, observable outcome>
- Context references: <specs, decisions, task brief, files, prior reports>
- Allowed scope: <paths/areas the role may change>
- Forbidden changes: <paths/areas/decisions out of scope>
- Dependencies: <task IDs and status, or `none`>
- Constraints: <approvals, conventions, time/tool limits>
- Expected artifacts: <files, reports, evidence>
- Acceptance criteria: <observable checklist>
- Return format: <report format reference>
- Escalation: <what must be escalated and to whom>
- Deadline/stop condition (optional): <when to stop and report>
```

Rules:

- One delegation has one objective and one accountable role.
- Context is linked, not pasted wholesale.
- Acceptance criteria are observable and match the task brief or a reviewed subset.
- Forbidden changes are explicit; "use good judgment" is not a boundary.
- A delegation that changes approved scope or acceptance criteria requires Orchestrator review, and material changes require user approval.
- Dependencies must be `done` or explicitly listed as read-only context.

## 5. Return and review payloads

### 5.1 Specialist return

```markdown
## Specialist Return — <delegation-id>
- Role / task:
- Objective restated:
- Status: complete | partial | blocked
- Changes: <files and purpose>
- Verification: <commands and observed output>
- Acceptance criteria: <criterion -> evidence>
- Risks / open questions:
- Proposed memory updates: <MUP references or `none`>
- Scope deviations: <none or explicit>
- Next action:
```

### 5.2 Manager review and report

```markdown
## Manager Report — <delegation-id>
- Domain / task:
- Units reviewed: <specialist return IDs>
- Review decision: accepted | revise | rejected
- Evidence checked: <specific artifacts/commands>
- Consolidated changes:
- Conflicts / risks:
- Scope deviations:
- Proposed memory updates:
- Recommendation to Orchestrator:
- Next action:
```

### 5.3 Review criteria

A Manager accepts a specialist return only when:

1. the objective and boundaries match the delegation;
2. every acceptance criterion maps to inspectable evidence;
3. verification commands were actually run and their output is reported;
4. no forbidden change occurred;
5. scope deviations are explicit and justified;
6. proposed memory updates follow the consolidation protocol;
7. risks and open questions are stated, not hidden;
8. the result is reproducible from the cited artifacts.

The Orchestrator applies the same criteria to the manager report and additionally checks it against the task brief, specs, and approved decisions (ORCH-007).

## 6. Memory and decision boundaries

- Specialists and Managers return **proposals**, not canonical writes. Proposals follow `memory-consolidation.md` §4.
- The Orchestrator (or designated steward) reviews and applies accepted proposals.
- Material decisions follow `decision-and-approval-protocol.md`; only the Orchestrator asks the user.
- Approved decisions are appended to `DECISIONS.md` with attribution.
- Task status changes follow `task-lifecycle.md`; `done` requires evidence for every criterion.
- Secrets, credentials, tokens, and unnecessary sensitive data never enter a report or memory record.

## 7. Escalation routes

| Situation | First stop | Escalates to | User involved? |
| --- | --- | --- | --- |
| Specialist needs clarification inside approved scope | Manager | — | No |
| Specialist finds scope/acceptance ambiguity | Manager | Orchestrator if it changes the task | Only if material |
| Specialist finds a material architecture/security/privacy issue | Manager | Orchestrator | Yes |
| Specialist is blocked by a dependency or missing input | Manager | Orchestrator | Only if it changes scope |
| Manager finds a spec/decision conflict | Manager | Orchestrator | Yes if material |
| Manager finds a cross-domain conflict | Manager | Orchestrator | Yes if material |
| Orchestrator finds conflicting user instructions | Orchestrator | User | Yes |
| Any role detects a secret or privacy exposure | Any | Orchestrator immediately | Yes if exposure occurred |
| Any role is asked to perform a destructive action | Any | Orchestrator | Yes; no action before approval |
| Provider capability cannot support required behavior | Manager | Orchestrator | Yes when it changes the plan |

Escalation rule: the escalation names the source, impact, options, and the one decision needed. It never asks the user directly below the Orchestrator.

## 8. Sequential fallback

When the provider cannot run nested subagents, or when the user does not opt into experimental depth, the same contracts run in one session in a fixed order.

### 8.1 Fallback sequence

1. **Orchestrator pass:** startup packet, classification, conflict check, delegation payload written to the task record.
2. **Manager pass:** decomposition, per-unit delegation payloads, review checklist prepared.
3. **Specialist pass:** execute one unit, produce a specialist return with evidence.
4. **Manager review pass:** apply §5.3, revise or accept, update the manager report.
5. **Orchestrator validation pass:** check the report against specs and acceptance criteria, apply accepted memory proposals, update task state, and respond to the user.

Repeat steps 3–4 per unit. The session may simulate the roles in one context, but it must produce the same artifacts and respect the same prohibitions.

### 8.2 Fallback rules

- Do not claim that separate agents ran when they did not.
- Keep each role's output in its own labeled section; do not blend specialist evidence into the Orchestrator's summary without review.
- A single model playing a Specialist must still not approve its own material decision or write canonical memory directly.
- If the model loses context between passes, reload from files; do not rely on recalled conversation.
- The fallback is the baseline; native delegation is an optimization.

### 8.3 Capability matrix

| Capability | Native delegation | Sequential fallback |
| --- | --- | --- |
| Orchestrator talks to user | Native Orchestrator agent | Same session, explicit Orchestrator pass |
| Manager coordinates | Native Manager agent | Manager pass with written delegation |
| Specialist executes | Native Specialist agent | Specialist pass per unit |
| Nested Manager → Specialist | Requires depth ≥ 2 | Always available |
| Review evidence | Native return message | Written specialist return + review section |
| Memory writes | Orchestrator/steward | Same; must be a separate pass |

## 9. Provider mapping boundaries

- The core defines roles, payloads, and invariants; adapters map them to native constructs.
- Possible mappings: subagents, agents, modes, skills, commands, or sequential prompts.
- An adapter must preserve B-01–B-10 or document the exact limitation and fallback.
- The core must not assume concurrency, nested delegation, a specific model, or a specific provider.
- Adapter-specific files live outside canonical `.blueprint/` memory and link back to it.
- If a provider cannot support a boundary, the adapter uses the sequential fallback rather than weakening the contract.

## 10. Reusable prompt templates

The following files are provider-neutral templates. Adapters may wrap or translate them but must not remove their authority boundaries.

| Template | Use |
| --- | --- |
| [`prompts/orchestrator.md`](../../prompts/orchestrator.md) | Startup, classification, delegation, validation, approval, consolidation. |
| [`prompts/manager.md`](../../prompts/manager.md) | Domain decomposition, specialist delegation, review, reporting. |
| [`prompts/specialist.md`](../../prompts/specialist.md) | Bounded execution and evidence-backed return. |
| [`prompts/delegation-payload.md`](../../prompts/delegation-payload.md) | Copyable delegation, return, and review structures. |

Prompt templates are role instructions, not canonical project memory. Project facts always come from the startup records.

## 11. End-to-end sample delegation

This sample exercises the contracts and is the TASK-008 verification scenario.

**Request (User → Orchestrator):** "Add a concurrency note to the memory protocol."

1. **Orchestrator** loads the startup packet, classifies the request as a change request, and checks the task graph. It finds TASK-007 owns concurrency semantics and that editing the normative protocol requires task scope. It creates or selects a task, then delegates to `MANAGER: Architecture` with objective, context, allowed scope (`docs/architecture/memory-protocol.md` §8 only), forbidden changes (no decision rewrite, no schema change), dependencies, artifacts, acceptance criteria, and return format.
2. **Manager** decomposes into one specialist unit: draft the note, verify links, propose the change. It writes a delegation with the same boundaries.
3. **Specialist** reads the current section, drafts the note, runs a link check, and returns changes, commands/output, criterion evidence, and a memory proposal. It does not commit canonical memory.
4. **Manager** reviews the return against §5.3, accepts or requests revision, and sends a manager report with the reviewed evidence and a recommendation.
5. **Orchestrator** validates against the task brief and SPEC-002, confirms no material decision is involved, applies the accepted proposal, updates `CURRENT_STATE.md`/registry if needed, records provenance, and replies to the user.

Boundary check: only the Orchestrator spoke to the user (B-01); the delegation was complete (B-02); the specialist did not write canonical memory (B-03) or approve anything (B-04); the manager reviewed evidence (B-05); the Orchestrator validated criteria (B-06); no material approval was bypassed (B-07); the same artifacts exist if run sequentially (B-08).

## 12. Acceptance evidence for TASK-008

| Criterion | Evidence |
| --- | --- |
| Orchestrator remains sole user-facing role | Invariant B-01; §3.2, §3.3, §3.4 prohibitions; §7 escalation routes. |
| Manager and Specialist boundaries are testable | B-02–B-06 and B-10; role contracts; §5.3 review criteria. |
| Delegations include scope, constraints, dependencies, outputs, acceptance criteria | §4 required fields and rules. |
| Sequential fallback is documented | §8 sequence, rules, and capability matrix; B-08 and §11. |
| Provider mapping does not assume parallel subagents | §9 boundaries; SPEC-003 AGENT-007/AGENT-008. |
