# Memory Consolidation and Concurrent Update Safeguards

- Status: accepted design baseline for TASK-007
- Date: 2026-11-04
- Specs: SPEC-002, SPEC-005
- Related: SPEC-004, `docs/architecture/memory-protocol.md`, `docs/architecture/decision-and-approval-protocol.md`, `docs/architecture/task-lifecycle.md`, `schemas/memory-metadata.schema.json`
- Applies to: initialized target projects under `.blueprint/`; this repository applies the same rules to root `/memory`, `/tasks`, `/specs`, `/sessions`, and `/handoffs`.

## 1. Purpose

Define how a specialist's durable memory change becomes a reviewed canonical write, how ownership and provenance are recorded, and how two agents that edit the same shared record are reconciled without losing history or silently overwriting each other.

The baseline in [memory-protocol.md](memory-protocol.md) §8 states that specialists propose changes and that last-write-wins is prohibited for decisions and task state. This document makes that baseline operational.

## 2. Principles

1. **Proposal before write.** A specialist never writes a shared canonical record directly. It submits a proposal with evidence.
2. **One owner per fact.** The ownership map in memory-protocol §5 decides where the fact belongs.
3. **Steward review.** The Orchestrator, or a Manager explicitly delegated as memory steward, reviews every proposal before it reaches canonical memory.
4. **Optimistic concurrency.** Every write carries the base content hash it was derived from. A changed base invalidates the write and forces reconciliation.
5. **Semantic merge, not line merge.** Facts, identifiers, and status are compared by meaning; a text merge that produces a valid file is not sufficient.
6. **No last-write-wins.** Decisions, task status, ownership, and scope are never resolved by timestamp or arrival order.
7. **Append and supersede.** Decision history, session history, and completion evidence are preserved. Corrections are additive.
8. **Git is the audit trail.** Applied changes are committed with traceable identifiers. Derived records may be rebuilt; canonical history may not be erased.
9. **No secrets.** Proposals and provenance must not contain credentials, tokens, private keys, or unnecessary personal data.

## 3. Roles and authority

| Role | May do | Must not do |
| --- | --- | --- |
| Specialist | Read canonical records; produce evidence; submit a memory update proposal. | Write shared canonical records directly; approve its own proposal. |
| Manager | Review specialist proposals in its domain; recommend accept/reject; propose spec/task/architecture changes. | Write shared canonical records outside an approved steward workflow; decide material conflicts alone. |
| Memory steward (Orchestrator by default) | Validate proposals, consolidate compatible changes, apply accepted writes, record provenance, escalate conflicts. | Approve material decisions reserved for the user; silently rewrite history. |
| Orchestrator | Own the canonical write, present material conflicts to the user, record approved decisions. | Treat a model preference or handoff claim as user approval. |
| User | Own product intent and material approvals. | — |

If no steward is designated, the Orchestrator is the steward. A Manager may act as steward only when `config/agents.json` records the delegation and the change is non-material.

## 4. Memory update proposal

### 4.1 Proposal lifecycle

```text
submitted → under_review → accepted → applied
                         ↘ rejected
                         ↘ superseded
            ↘ withdrawn
```

- `submitted`: complete enough to review.
- `under_review`: a steward has claimed it; no other steward applies it.
- `accepted`: reviewed and approved for application.
- `applied`: written to the owning record and committed.
- `rejected`: recorded with a reason; the proposal is retained.
- `superseded`: a newer proposal replaces it before application.
- `withdrawn`: the proposer removed it before review completed.

Only `accepted` proposals may be applied. A proposal is not a fact until `applied`.

### 4.2 Proposal record format

Proposals are appended to the active task brief's execution log, or to the session record when no task is active. They are Markdown so they diff and review in Git.

```markdown
### Memory Update Proposal MUP-YYYYMMDD-NN
- Status: submitted | under_review | accepted | rejected | applied | superseded | withdrawn
- Proposer: SPECIALIST: <role> | MANAGER: <role>
- Task: TASK-NNN (or `none` with justification)
- Target record: `.blueprint/<path>`
- Fact class: project | architecture | decision | convention | current-state | task-status | task-evidence | session | handoff
- Change type: create | append | modify | supersede
- Base version: sha256:<hash of the target record when read>
- Fact: <one sentence, durable, observable>
- Evidence: <command/output, file path, review artifact, or external URL with access date>
- Proposed change: <diff, appended section, or exact replacement text>
- Conflict check: <records and tasks checked; conflicts found or `none`>
- Requested approval: <none | ADR needed | user approval needed>
- Steward review: <reviewer, date, decision, rationale>
- Applied change: <commit hash and final sha256, or `not applied`>
```

Rules:

- One proposal changes one owning record or one tightly coupled set. Do not bundle unrelated facts.
- The fact is written as a proposition, not as a preference or a question.
- The base version is mandatory for `modify` and `supersede`; `create` records `absent`.
- A proposal that cannot name its evidence is not reviewable and stays out of canonical memory.
- Status is updated in place as the proposal moves through review; the history remains in the task brief or session log.

### 4.3 Intake checks

A steward rejects or returns a proposal when:

1. the target is not the owning record for the fact;
2. the base version does not match the current record;
3. the evidence is missing, stale, or for a different claim;
4. the change alters approved scope, architecture, security, privacy, or data ownership without the required approval;
5. the proposal duplicates a fact already owned elsewhere;
6. the proposal contains a secret or unnecessary sensitive data;
7. the change would delete or rewrite canonical history instead of appending or superseding;
8. the task status transition is invalid under `task-lifecycle.md` §4–§5.

## 5. Ownership and provenance

### 5.1 Ownership

Ownership is defined once by the ownership map and reflected in `memory/metadata.json` (`owner_role`, `class`, `last_updated`, `last_task`, optional `sha256`). If two records claim the same fact, the owner named by the map wins; the other record is corrected to link, not duplicate.

### 5.2 Provenance fields

Every applied canonical change must be traceable to all of the following:

| Provenance element | Recorded in |
| --- | --- |
| Who proposed the change (role, not personal identity) | Proposal `Proposer` and task brief/session log |
| Which task authorized it | Proposal `Task`; `metadata.json` record `last_task` |
| What evidence supported it | Proposal `Evidence`; task completion evidence for task work |
| What record and owner were affected | `metadata.json` record `path`, `owner_role`, `class` |
| The base the change was derived from | Proposal `Base version` |
| What was actually written | Git commit that applies the change; `metadata.json` `sha256` when maintained |
| Who reviewed and when | Proposal `Steward review`; task execution log |
| Which approval applied | ADR ID for material decisions, task approval otherwise |
| What it replaced, if anything | `Supersedes`/`Superseded by` in `DECISIONS.md`; new correction in sessions/handoffs |

### 5.3 Commit traceability

The commit that applies a proposal includes a body trailer identifying the proposal and task, for example:

```text
memory: record approved authentication boundary

Memory-Proposal: MUP-20261104-01
Task: TASK-021
Reviewed-by: ORCHESTRATOR
```

Git history is immutable and is the final audit trail. Do not force-push over canonical history. `metadata.json` remains a pointer record; it never replaces the commit history.

### 5.4 Provenance retention

- `metadata.json` keeps current pointers and timestamps only; it does not accumulate a change log.
- The task brief or session record retains the proposal and review outcome.
- `DECISIONS.md` retains material decisions permanently.
- `sessions/*.md` and `handoffs/*.md` are historical; correct them with a new record, not by rewriting the old one.
- A change without a proposal record is a process violation; the steward must reconstruct the provenance before later changes rely on it, and record the reconstruction.

## 6. Consolidation workflow

1. **Receive.** A manager forwards a specialist proposal, or the steward reads it from the task brief.
2. **Locate owner.** Apply the ownership map; confirm the target record and field.
3. **Freeze the base.** Record the current hash and `git status` for the target.
4. **Validate evidence.** Confirm the evidence supports the exact fact proposed.
5. **Classify the change:**
   - *additive* — new facts, new decision, new task, new evidence;
   - *corrective* — fixes a stale or wrong fact without changing intent;
   - *superseding* — replaces a decision or convention while preserving history;
   - *material* — changes architecture, scope, security, privacy, ownership, compatibility, or cost.
6. **Check authority.** Material changes require the approval workflow in `decision-and-approval-protocol.md`. If approval is missing, mark the proposal `under_review` and record a pending approval; do not apply.
7. **Merge semantically.** Apply §7. Reject stale bases.
8. **Write the owner.** Apply the change to the owning record only.
9. **Synchronize projections.** Update `CURRENT_STATE.md`, registry/backlog, metadata, or task evidence only as required by memory-protocol §6.1.
10. **Record provenance.** Complete the proposal's `Steward review` and `Applied change`; append the application to the task execution log.
11. **Verify.** Re-read the record, validate JSON/schemas/links, and confirm status and evidence agree.
12. **Commit.** Use the §5.3 trailer. Never commit secrets.

## 7. Concurrent update reconciliation

### 7.1 Detection

A concurrent change exists when any of the following is true:

- the current target hash differs from the proposal's base version;
- `git status` or `git diff` shows the target changed since it was read;
- a Git merge or rebase reports a conflict;
- the registry, task brief, and `CURRENT_STATE.md` disagree;
- two proposals target the same record or field;
- two tasks are `in_progress`, or a task status is changed by two sessions.

Detection always pauses application. Do not overwrite the other change to make the diff disappear.

### 7.2 Classification of the collision

| Class | Meaning | Resolution |
| --- | --- | --- |
| Disjoint | Different records, or different fields/facts with no dependency. | Merge both after revalidating each base. |
| Compatible | Same intent, non-conflicting wording or additive sections. | Steward merges into one coherent edit, preserving both sources. |
| Duplicate | Same fact proposed twice. | Keep one; record the other as duplicate with a link. |
| Stale base | Base hash changed but the proposed fact is unaffected. | Rebase the proposal onto the new content, revalidate, re-apply. |
| Semantic conflict | Same fact, different values, or incompatible status. | Stop; steward decides non-material cases, user decides material cases. |
| History rewrite | A proposal deletes, truncates, or rewrites canonical history. | Reject; require append or supersede. |

### 7.3 Semantic merge procedure

1. **Stop writes** to the contested record and anything derived from it.
2. **Read all versions:** the common base (if available), the current canonical content, and the proposal.
3. **Compare facts, not lines.** For each changed fact record `(record, field, value, source, evidence)`.
4. **Apply the merge rule:**
   - disjoint facts → union;
   - identical value → keep one;
   - different value for the same fact → conflict, do not choose by timestamp;
   - additive list (decisions, evidence, sessions, handoffs) → include both, preserving order by date and then ID;
   - task status → the registry is authoritative only when the recorded transition is valid and evidenced; otherwise treat it as a state conflict and stop;
   - ownership → the ownership map decides; never let a proposal reassign ownership by assertion.
5. **Renumber collisions.** If both sides append the same ID (for example `ADR-008`), keep both records and renumber the later one, adding reciprocal links so neither is lost.
6. **Revalidate.** Run JSON/schema/link/dependency checks after the merge, not before.
7. **Record the reconciliation.** Append a short note to the task brief or `CURRENT_STATE.md`: what collided, how it was resolved, and which sources survived. Material outcomes get an ADR.
8. **Resume.** Continue only after the merged record and its projections agree.

### 7.4 Prohibited resolutions

- Choosing the later timestamp or the later-arriving session.
- Discarding one version because it is inconvenient.
- Rewriting `DECISIONS.md`, session history, handoff history, or completed evidence to remove a conflict.
- Forcing a valid-looking file when the underlying facts still disagree.
- Applying a proposal whose base version is stale without re-deriving it.
- Letting a specialist approve its own proposal or write the shared record directly.

## 8. Append-only records and history

| Record | Rule |
| --- | --- |
| `DECISIONS.md` | Append only. Correct by adding a superseding ADR and cross-linking. Never delete or rewrite an accepted ADR. |
| `sessions/*.md`, `handoffs/*.md` | Historical. Add a correction record; do not rewrite the original. |
| Task completion evidence | May be extended; never deleted to hide a failed check. A failed verification is recorded as a failure. |
| `registry.json` status | Transitions are persisted in order. Do not erase a blocked/in_review history that explains the current state. |
| `metadata.json` | Current pointers only; Git history carries the audit trail. |
| Derived indexes/caches | Rebuildable and non-authoritative; never edit to override canonical content. |

## 9. Failure handling

| Condition | Required behavior |
| --- | --- |
| Base hash mismatch | Reject as stale; re-read, re-derive, re-review the proposal. |
| Target has uncommitted user changes | Preserve them; merge or ask; never discard. |
| Two stewards claim the same proposal | First claimant owns `under_review`; the second stops and links. |
| Proposal lacks evidence | Reject; do not infer the fact. |
| Material change without approval | Keep `under_review`; record pending approval; do not apply. |
| Conflicting task status | Stop and report a state conflict; registry wins only after valid, evidenced reconciliation. |
| Git merge conflict in canonical memory | Resolve semantically per §7; never accept "ours" or "theirs" wholesale. |
| Secret detected in a proposal or record | Stop; remove/redact before commit; record the incident if exposure occurred. |
| Record and projection disagree after application | Blocking integrity error; reconcile before further writes. |

## 10. Scenario simulations

These scenarios verify the protocol. They are review scenarios until the TASK-014 validator exists.

### 10.1 Two incompatible proposals for the same fact

**Input:** Specialist A proposes "production uses PostgreSQL"; Specialist B proposes "production uses SQLite" against the same `PROJECT_CONTEXT.md` base.

**Expected:** Both proposals name the same fact with different values. The second application detects a semantic conflict and stops. The steward does not accept either by timestamp. If the choice is material (data ownership/architecture), the Orchestrator asks the user; the approved option is applied and recorded as an ADR; the other proposal is `rejected` with a link. History shows both proposals and the decision.

### 10.2 Stale base, unaffected fact

**Input:** A proposal modifies `CURRENT_STATE.md` next action. Meanwhile another session appends an unrelated blocker to the same file.

**Expected:** The hash mismatch is detected, the class is *stale base* (the proposed next-action fact is unaffected), the proposal is rebased onto the current content, and both the blocker and the next action survive. The reconciliation note records the rebase.

### 10.3 Disjoint records

**Input:** One specialist proposes an ADR; another proposes task evidence in a different task brief.

**Expected:** Apply both. No collision; each proposal has its own owner and base. Independence is still verified because both may affect `CURRENT_STATE.md` projections.

### 10.4 Duplicate ADR IDs

**Input:** Two branches both append `ADR-008`.

**Expected:** Keep both decisions, renumber the later one to `ADR-009`, add `Supersedes`/`Related` links as appropriate, and record the renumbering. No decision is lost.

### 10.5 Task status conflict

**Input:** One session sets `TASK-021` to `done`; another sets it to `blocked`.

**Expected:** Conflict detected. `done` is accepted only if every criterion has evidence; otherwise it is invalid. `blocked` requires reason, responsible role, and next action. If both are evidenced and contradictory, stop and report a state conflict; do not pick one by arrival order. A material resolution is recorded.

### 10.6 Specialist direct write attempt

**Input:** A specialist edits `.blueprint/memory/ARCHITECTURE.md` directly.

**Expected:** Rejected by policy. The change is reverted or treated as a proposal with no authority; the specialist must submit a proposal. The Orchestrator records the process violation if it reached a commit.

### 10.7 Deletion request

**Input:** A proposal asks to delete an inconvenient accepted ADR.

**Expected:** Rejected. The correct action is a superseding ADR that preserves the old one and links the replacement.

## 11. Relationship to validation

TASK-014 (validation and conformance) should check at least:

- every canonical record has a `metadata.json` entry with an owner and `last_updated`;
- `last_task` resolves to an existing task;
- `DECISIONS.md` has unique ADR IDs and valid supersession links;
- task status transitions follow the lifecycle matrix;
- registry, briefs, and `CURRENT_STATE.md` agree;
- no canonical record is missing while referenced by metadata;
- no secret patterns appear in canonical records.

Proposal lifecycle state is review metadata, not a required JSON schema field at this baseline. If machine-readable proposals are later required, introduce a versioned schema under `schemas/` rather than overloading `metadata.json`.

## 12. Acceptance evidence for TASK-007

| Criterion | Evidence |
| --- | --- |
| Specialist updates are proposals until reviewed | §3 authority table, §4 lifecycle and intake checks, §10.6. |
| Memory ownership and provenance are recorded | §5 ownership and provenance fields, §5.3 commit trailers, §5.4 retention. |
| Concurrent edits have a reconciliation protocol | §7 detection, classification, semantic merge, prohibited resolutions; §10.1–§10.5. |
| Decision history is preserved | §8 append-only rules, §10.4 duplicate IDs, §10.7 deletion request. |
