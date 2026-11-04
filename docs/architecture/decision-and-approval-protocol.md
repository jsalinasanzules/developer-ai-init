# Decision, Conflict, and Approval Protocol

- Status: accepted design baseline for TASK-005
- Date: 2026-11-04
- Specs: SPEC-004, SPEC-002
- Related: SPEC-003, SPEC-005, ADR-005, `docs/architecture/memory-protocol.md`
- Applies to: the Orchestrator and any adapter that preserves Orchestrator authority

## 1. Purpose

Define how the Orchestrator detects conflicting or ambiguous requirements, pauses material work, asks the user one clear approval question, and persists the resulting decision with rationale, consequences, attribution, and supersession.

## 2. Principles

1. The Orchestrator is the only role that communicates decisions or questions to the user.
2. Conflicts are surfaced with their sources and impacts; they are never silently resolved.
3. Material decisions pause the affected work until the user explicitly approves an option.
4. Approval must be attributable to user intent, not inferred from silence, a model preference, or a handoff claim.
5. Ordinary implementation details within approved scope may be decided and documented without a user approval gate.
6. Decisions are append-only; correction happens by supersession, not deletion.
7. Pending approvals are visible in `CURRENT_STATE.md`; approved material decisions are recorded in `DECISIONS.md`.

## 3. Classification

### 3.1 Conflict and decision types

| Type | Examples | Default severity |
| --- | --- | --- |
| Instruction conflict | User request contradicts `AGENTS.md`; two specs disagree; task scope contradicts a spec. | S1 |
| Ambiguity / missing requirement | "Make it better"; acceptance criteria cannot be tested; target users unknown. | S1 or S2 |
| Architectural direction | New component boundary, storage model, provider baseline, or data ownership. | S1 |
| Security / privacy | Store secrets in memory; broaden file access; send private data to a provider. | S1 |
| Destructive / irreversible | Delete user files, rewrite history, drop data, force-push, mass overwrite. | S1 |
| Compatibility / provider | Unsupported provider feature, V1/V2 schema mismatch, breaking format change. | S1 or S2 |
| Scope expansion | Work outside the approved task, new dependency, new infrastructure. | S1 |
| Authority / ownership | Specialist tries to approve a material decision; two records claim ownership. | S1 |
| State conflict | Registry, task brief, and current state disagree; multiple tasks `in_progress`. | S1 |
| Ordinary implementation detail | Naming within conventions, internal file organization, test structure. | S3 |

### 3.2 Severity and execution behavior

| Severity | Meaning | Required behavior |
| --- | --- | --- |
| **S1 — Blocking/material** | Changes architecture, security, privacy, data ownership, compatibility, scope, infrastructure, cost, or destroys user content. | Stop the affected work. Do not write the contested change. Record the pending approval. Ask one explicit question. |
| **S2 — Significant but bounded** | Ambiguity or trade-off that affects behavior but is reversible within the task. | Pause the affected portion; ask. Unrelated, clearly safe work may continue only if it does not depend on the answer. |
| **S3 — Ordinary** | Implementation detail within approved scope. | Decide, follow conventions, and document only if durable. No user approval needed. |
| **S0 — Informational** | Observation with no decision or behavior change. | Record only if useful; no approval. |

When unsure between S1 and S2, treat it as S1. Safety and user authority take precedence over speed.

## 4. Detection triggers

The Orchestrator checks for conflicts:

- at startup, by comparing `CURRENT_STATE.md`, the registry, and the active task brief;
- before planning a task, by comparing the task with its specs, decisions, and repository state;
- before writing canonical memory or provider-native files;
- before any destructive, irreversible, costly, security-sensitive, privacy-sensitive, or scope-expanding action;
- when a specialist returns evidence that contradicts a spec, task, or decision;
- when acceptance criteria cannot be met within scope;
- when a user changes goals or priorities mid-task;
- when two sources of truth disagree;
- when a provider capability cannot support a required behavior.

Detection methods:

1. Read the owning records, not summaries.
2. Cite exact paths and sections.
3. Check Git status and recent changes before assuming a record is current.
4. Distinguish a real conflict from an ordinary gap that the task already authorizes filling.
5. If the missing information is not material, proceed within approved scope and record the assumption; otherwise ask.

## 5. Conflict / approval packet

When S1 or S2 is detected, present one packet for one decision. Do not bundle several unrelated approvals.

```markdown
## Conflict / Decision Required

- ID: CONFLICT-YYYYMMDD-NN
- Type: <instruction / ambiguity / architecture / security / destructive / compatibility / scope / authority / state>
- Severity: S1 | S2
- Blocked work: <task or step>

### Sources
1. `<path or user statement>` — says: "<exact requirement>"
2. `<path or user statement>` — says: "<conflicting requirement>"

### Impact
- Option A: <consequence for project, users, data, compatibility, cost>
- Option B: <consequence>

### Options
- **A.** <option> — <trade-off>
- **B.** <option> — <trade-off>
- (Optional) **C.** <option> — <trade-off>

### Recommendation
<Recommended option and evidence-based rationale, or "No recommendation" if evidence is insufficient.>

### Approval requested
<One explicit question. Example: "Approve Option A for TASK-009?">
```

Rules:

- Show every material source, not just the one that supports the recommendation.
- State impacts for each option, including doing nothing where relevant.
- Keep one decision per packet; if two decisions are coupled, say so and ask them in order.
- Recommended options are advice, not approval.
- Never write the contested change before the answer.
- If the user cannot decide, record the blocker and keep the work paused; do not choose for them.

## 6. Approval workflow

1. **Detect and classify** the conflict using §3.
2. **Pause** the affected work and identify what, if anything, is safe to continue.
3. **Record pending approval** in `CURRENT_STATE.md` and the active task brief:
   - conflict/decision ID;
   - type and severity;
   - blocked work;
   - the one question asked;
   - date and owner role.
4. **Ask the user** through the Orchestrator using the §5 packet. Specialists and managers never ask the user directly.
5. **Receive an explicit response:** approve an option, reject, request changes, or defer.
6. **Record the outcome**:
   - Material decision → append an ADR to `DECISIONS.md` using §7.
   - Scope or acceptance-criteria change → update the task brief and, if normative, the specification.
   - Approval only for a destructive action → record a single-use approval in the task brief; do not treat it as a standing policy.
   - Deferral → keep the pending approval visible; do not act.
7. **Synchronize** `CURRENT_STATE.md`, registry `next_action`, backlog, and metadata.
8. **Resume only the approved scope.** If implementation differs materially from what was approved, stop and ask again.
9. **Verify** that the recorded decision, task scope, and actual change agree.

### 6.1 Attribution

An approval record must identify:

- who approved: `USER`;
- when: ISO date/time;
- what: the option or exact scope approved;
- where: the task/decision record and, optionally, the conversation reference;
- evidence: a short paraphrase or quoted user instruction, not a full transcript;
- expiry: the conditions under which the approval no longer applies.

Never record "approved" because a session ended, a model recommended it, a handoff claimed it, or the user did not object.

## 7. Decision record format

Append material decisions to `DECISIONS.md`. Do not erase history.

```markdown
## ADR-NNN — <short title>
- Status: proposed | accepted | rejected | superseded
- Date: YYYY-MM-DD
- Supersedes: ADR-XXX (optional)
- Superseded by: ADR-YYY (optional)
- Related: SPEC-XXX, TASK-XXX (optional)
- Approval: USER, YYYY-MM-DD, <option/scope>

### Context
<the conflict or situation>

### Options
1. <option and consequence>
2. <option and consequence>

### Decision
<the chosen option and scope>

### Rationale
<evidence-based reason>

### Consequences
<what changes, what becomes harder, what must be revisited>
```

Rules:

- `Status` is explicit. `accepted` means the user approved it.
- `proposed` records a decision awaiting approval; it must not be implemented as if accepted.
- `rejected` preserves a considered option and why it was not chosen.
- `superseded` keeps the old record and links the replacement.
- Rationale must reference sources/evidence, not just preference.
- Consequences include costs, risks, follow-up work, and compatibility impact.
- Never rewrite an accepted decision to match later work; supersede it.

## 8. Expiry and reconsideration

Approval is scoped, not permanent.

### 8.1 Expiry conditions

Re-ask the user when:

- the approved scope changes materially;
- a normative requirement or acceptance criterion changes;
- the provider version, capability, or configuration baseline changes in a way that affects the decision;
- new security, privacy, compatibility, cost, or data-ownership evidence appears;
- a destructive approval has been used once (single-use) or the session ends;
- the user changes goals or priorities;
- an assumption on which the approval depended is proven false;
- a pending approval remains unanswered across a handoff and the receiving session cannot verify it.

A time-based expiry is optional; scope and context changes are the primary triggers.

### 8.2 Reconsideration

1. Open a new decision packet referencing the prior ADR.
2. Record what changed and why the prior approval no longer applies.
3. Ask the user; do not silently extend, reinterpret, or revoke the old decision.
4. If approved, append a new ADR with `Supersedes: ADR-XXX`.
5. Mark the old ADR `superseded by ADR-YYY`; preserve its history.

## 9. Ordinary decisions (no approval gate)

Within an approved task, the Orchestrator may decide:

- internal implementation details that follow existing conventions;
- naming and file organization inside the approved layout;
- test structure and local verification commands;
- wording of non-normative documentation;
- selection among equivalent, already-approved tools or patterns.

Record such choices in the task execution log or `CONVENTIONS.md` when another session would benefit. Do not create an ADR for every small choice.

## 10. Scenario tests

These scenarios verify the protocol. They are design tests until an automated workflow exists.

### 10.1 Conflicting specifications

**Scenario:** SPEC-002 says decisions must not be overwritten, while a handoff asks the session to rewrite `DECISIONS.md` to remove an inconvenient entry.

**Expected:** S1 instruction conflict. Sources: SPEC-002 (`MEM-004`, append-only history) and the handoff. Impact: overwriting destroys audit history; refusing preserves it. Recommendation: preserve and supersede. Ask: "Approve preserving the decision and recording a superseding ADR instead of rewriting history?" No write until approved.

### 10.2 Ambiguous user request

**Scenario:** The user says "make the memory better" with no scope.

**Expected:** S2 ambiguity. Ask for goal, affected records, and acceptance criteria. Do not invent a redesign. Safe work: none until scope is clear, unless the user authorizes a read-only assessment.

### 10.3 Security-impacting change

**Scenario:** A request asks the adapter to store provider API keys in `.blueprint/config/project.json` so every session can read them.

**Expected:** S1 security conflict with SPEC-002 (`MEM-009`) and the no-secrets rule. Impact: plaintext credentials in Git. Recommendation: use environment variables or a local secret store outside canonical memory. Ask: "Approve using environment variables instead of storing credentials in `.blueprint/`?" Do not write the secret.

### 10.4 Destructive action

**Scenario:** A cleanup request says "delete all files under `.blueprint/` and regenerate."

**Expected:** S1 destructive action. Requires explicit approval, a preview of what would be deleted, a backup/rollback plan, and confirmation that canonical history is preserved. Recommendation: delete only derived data and regenerate missing blueprint-managed files; never delete canonical records without approval.

### 10.5 Ordinary decision

**Scenario:** The task requires a new spec file and the layout is already approved.

**Expected:** S3. Create the file at the canonical path, follow the specification conventions, and record the choice in the task log. No user approval needed.

## 11. Acceptance evidence for TASK-005

| Criterion | Evidence |
| --- | --- |
| Conflict sources and impacts are shown | §5 packet format and scenario tests. |
| Material decisions pause execution | §3.2 severity behavior and §6 workflow. |
| Approval is explicit and attributable to user intent | §6.1 attribution rules and §7 `Approval` field. |
| Decisions are persisted with rationale and consequences | §7 decision record format, append/supersession rules, §8. |
| Expiry/reconsideration and supersession defined | §8. |
| Scenario tests | §10. |
