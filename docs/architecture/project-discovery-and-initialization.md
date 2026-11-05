# Project Discovery and Interactive Initialization

- Status: design baseline for TASK-012
- Date: 2026-11-05
- Specs: SPEC-008, SPEC-001
- Related: TASK-002, TASK-020, ADR-001, ADR-005, ADR-009
- Scope: discovery and approval protocol before a future initializer writes files

## 1. Purpose and boundaries

This document defines how an Orchestrator discovers a target repository,
interviews its user, records uncertainty, confirms a project summary, and
previews a safe initialization plan. It specifies behavior; it does not
implement an initializer or authorize TASK-013/TASK-014 work.

The Orchestrator is the only role that asks the user questions or accepts
approvals. Discovery is read-only. No canonical or provider-native project files
are generated until the user confirms both the project summary and a separate
write plan.

Initialization has four distinct outputs:

1. A sourced discovery inventory, which distinguishes observed facts from
   user-confirmed facts, assumptions, unknowns, and questions.
2. A confirmed project summary that can seed canonical records.
3. A path-by-path write plan classified as `CREATE`, `MERGE`, `SKIP`, or
   `CONFLICT`.
4. An approval record for the exact summary and exact planned operations.

An accepted summary does not authorize file changes. Approval of a write plan
does not authorize an unapproved overwrite, deletion, migration, or other
material change.

## 2. Terms and evidence

| Classification | Meaning | Permitted use |
| --- | --- | --- |
| Observed | Directly visible in a path, configuration, or repository metadata; include the path and observation method. | Present as a discovery result, not as user intent. |
| User-confirmed | The user explicitly confirms or supplies it. | Include in the proposed project context. |
| Assumption | A proposal not yet confirmed by the user. Record its rationale and mark it pending. | Never treat as a fact or use to authorize a material choice. |
| Unknown | Not observed or answered. Name what is unknown and whether it blocks a requested result. | Preserve as unknown; ask or pause rather than infer. |
| Question | A specific user input needed to resolve an unknown or confirm intent. | Ask through the Orchestrator; record unanswered questions as pending. |

Every discovered technology, convention, architecture boundary, or constraint
shown as a project fact must cite its evidence (for example, `pyproject.toml`
declares Python dependencies or `src/` contains application code). A marker file
may be stale or incomplete; describe what it proves and ask the user to confirm
whether it reflects the active project. Do not execute project scripts, install
dependencies, access a network, or read likely secret files as part of default
discovery.

## 3. Preflight and project classification

Before asking project questions, inspect the user-selected target and report its
resolved path. Do not silently substitute the current working directory. Limit
inspection to paths needed to identify the project and planned destinations.
Exclude generated/vendor directories such as `.git`, `node_modules`, `.venv`,
`vendor`, `dist`, and build output from broad inventory; preserve them.

Classify the target into exactly one starting condition:

| Starting condition | Observable definition | Flow |
| --- | --- | --- |
| Greenfield / empty | Target is absent, empty, or contains only repository metadata and no meaningful project artifacts. | Ask the project interview; no stack or conventions are presumed. |
| Brownfield / existing | Target contains source, configuration, documentation, or other user-owned project files. | Inventory evidence, then confirm it with the user during the interview. |
| Already initialized | `.blueprint/` exists and has a readable supported manifest. | Inspect installed version and state; use the existing-project flow, not a fresh-install flow. |
| Needs reconciliation | `.blueprint/` exists but its manifest is absent, invalid, or unsupported, or canonical records conflict. | Stop before writes. Report the exact discrepancy and request reconciliation/upgrade direction. |

Presence of `.git` alone does not mean that the repository is a populated
project. Conversely, an existing project need not have Git metadata. A target
path, symlink, permission, or root ambiguity that prevents safe path ownership
checks blocks planning.

### 3.1 Read-only inventory

For a brownfield or already-initialized project, inventory only relevant
evidence:

- Repository root, Git presence, and a bounded top-level directory/file listing.
- Language and tool candidates indicated by conventional manifests or lockfiles
  (for example `package.json`, `pyproject.toml`, `go.mod`, or `Cargo.toml`).
- Source, test, documentation, build, and deployment directory names.
- Architecture/convention documents and project-local agent instructions.
- Existing provider configuration and plugin paths for adapters the user names
  or that are directly relevant to the requested integration.
- Existing `.blueprint/` manifest, schema version, and required canonical
  records, when present.
- Candidate constraints explicitly encoded in checked-in config (for example a
  supported runtime range), with the exact source path.

Do not infer architecture, intended users, business goals, deployment targets,
security policy, preferred model/provider, or acceptance criteria solely from
file names or dependency markers. Do not claim a framework is active solely
because a dependency is present. Present evidence as candidates for user
confirmation. Record unavailable, conflicting, or stale evidence as unknown
or conflict.

## 4. Interview and draft model

Ask short, grouped questions in a stable order. Reuse user-confirmed answers and
validated repository evidence; do not ask the user to repeat known facts.

1. **Identity and purpose:** project name/slug, one-sentence purpose, intended
   users, goals, non-goals, and lifecycle/status.
2. **Scope and success:** what is in scope, what is excluded, and what outcome
   would demonstrate success.
3. **Technology and architecture:** confirm observed languages, frameworks,
   components, data stores, interfaces, architecture boundaries, and source
   conventions; ask about missing or ambiguous choices.
4. **Constraints:** supported environments, compatibility, security/privacy,
   data ownership, performance, licensing, budget, and operational limits.
5. **Agent/provider preferences:** selected provider(s), primary/optional/
   future role, and any requested delegation or integration preferences.
   Provider/runtime defaults are not selected on the user's behalf.
6. **Initial work:** candidate tasks only after scope and measurable acceptance
   criteria are clear. Unclear ideas remain questions or proposals, not tasks.

For every answer, record its classification and source. A blank, skipped,
declined, contradictory, or "I don't know" answer remains unknown; it is not
filled from a model's preference. Allow the user to defer any non-blocking
question. Identify which unknowns block a safe or coherent initialization and
which can remain explicitly unresolved in `project.json`.

### 4.1 Required identity fields and initialization status

The interview asks for a one-sentence project purpose. By default, after the
user confirms that sentence, use its exact text for both required scalar fields
`project.description` and `purpose.summary`; do not ask for the same fact
twice. If the user wants those fields to differ, ask for and confirm each value
separately. Never infer either value or generate a placeholder. The other
required scalars (`project.name`, `project.slug`, and `project.status`) must
also be explicitly confirmed before generating `project.json`.

Apply the project schema and cross-reference rule R-PROJ-02 exactly:

- Use `initialization.status: "complete"` only when
  `initialization.unknowns` is empty.
- Use `initialization.status: "partial"` only when the unknowns array is
  non-empty, every remaining unknown is non-blocking for the confirmed scope,
  all required scalar fields are confirmed, and the user approves the partial
  summary and write plan.
- Do not generate project files while any unknown blocks safe or coherent
  initialization.
- This flow does not write `initialization.status: "pending"` to
  `project.json`. Before summary and plan approval, the intake remains an
  ephemeral draft or an explicitly approved handoff, not canonical project
  state.

Map confirmed intake data to the existing canonical owners; do not add fields
to `project.json` that are not in
[`project.schema.json`](../../schemas/project.schema.json):

| Intake data | Canonical destination |
| --- | --- |
| Project name, slug, description, status, purpose summary, users, goals, non-goals, stack, constraints, provider selections, initialization status, unknowns, and accepted assumptions | `.blueprint/config/project.json`, using only the schema-defined fields. |
| Project-wide scope, domain vocabulary, and narrative context | `.blueprint/memory/PROJECT_CONTEXT.md`. |
| Confirmed architecture, components, boundaries, and data ownership | `.blueprint/memory/ARCHITECTURE.md`. |
| Coding, testing, documentation, and operational conventions | `.blueprint/memory/CONVENTIONS.md`. |
| Normative project requirements and measurable project-level success criteria | `.blueprint/specs/SPEC-<NNN>-<slug>.md`; create initial tasks only when their scope and acceptance criteria are clear. |

Structured fields in `project.json` and their narrative counterparts must agree;
the owning record and synchronization rules in the target layout remain in
force. The schema does not turn an inferred value into a fact. Only
user-confirmed facts are copied as project facts. Retain an assumption only when
the user explicitly accepts it as an assumption. Do not store credentials,
tokens, secrets, or unnecessary personal data.

The schema requires non-empty `project.name`, `project.slug`,
`project.description`, and `purpose.summary`, plus `project.status` from its
declared enum. If any is unknown or unconfirmed, pause and ask; do not invent a
placeholder or generate an invalid `project.json`. A partial initialization is
permitted only after every required scalar is confirmed and the user approves
the plan. It may retain non-blocking unknowns with
`initialization.status: "partial"` and field-specific entries in
`initialization.unknowns` (for example, `"stack: not yet confirmed"`). Use
`"complete"` only when `initialization.unknowns` is empty, as required by
R-PROJ-02.

For schema-defined arrays (`purpose.users`, `purpose.goals`,
`purpose.non_goals`, `stack`, `constraints`, and `providers`), an empty array
without a matching unknown entry means the user confirmed no applicable values.
If the answer is unknown or deferred, keep the array empty and record the
specific field in `initialization.unknowns`; consumers must consult both the
array and initialization state. An unresolved array-valued field that blocks
the requested scope pauses generation rather than being represented as a
confirmed empty value.

## 5. Summary and confirmation gate

Before constructing any file-write plan, present a concise summary containing:

- Target path and classification (greenfield, brownfield, already initialized,
  or needs reconciliation).
- User-confirmed purpose, users, goals, non-goals, scope, stack, architecture,
  constraints, and provider preferences.
- Observed candidates with their evidence paths and any user corrections.
- Explicit assumptions and unknowns, identifying which ones block progress.
- Proposed initial tasks, each with a concrete objective and measurable
  acceptance criteria, or a statement that no initial tasks are ready.
- Any unresolved decision or conflict and its approval requirement.

Ask the user to confirm, correct, defer, or cancel the summary. Only an explicit
confirmation of the current summary revision passes this gate. A correction
creates a new revision that must be confirmed. Silence, a partial answer, or
confirmation of an earlier revision is not approval.

If a blocking unknown, material conflict, or unsupported version remains,
summarize the blocker and stop before generating files. Do not hide the blocker
by converting it into an assumption. For non-blocking unknowns, the user may confirm a partial initialization; the
generated project must be marked `initialization.status: "partial"` with those
unknowns retained. If the unknowns array is empty, mark it `complete`. These
status values are assigned only after the user confirms the summary and
approves the write plan.

## 6. Destination inventory and collision preview

Only after summary confirmation, derive the candidate file set from the
canonical target layout and user-approved adapters. Before any write, inspect
every destination and classify it using the target layout's collision policy:
`absent`, `identical`, `user-modified`, `unknown`, or `conflict`. Display a
path-by-path preview using the TASK-020 generator outcomes:

| Preview outcome | Required meaning | Default handling |
| --- | --- | --- |
| `CREATE` | Destination is absent and the planned file is within the confirmed scope. | May proceed only after the user approves the complete write plan. |
| `MERGE` | A supported, deterministic merge preserves user-owned content and has no unresolved semantic collision. Show the proposed result/diff and affected user content. | Require explicit approval of the merge operation in the write-plan approval. |
| `SKIP` | Destination is already identical/current, or is explicitly outside the selected scope and will remain untouched. State which reason applies. | Do not write that path. |
| `CONFLICT` | Same-path semantics are incompatible, the file is user-edited in a way that cannot be safely merged, the version is unsupported, or a path/symlink collision prevents safe ownership. | Stop the whole plan before writing. Explain the conflict and request a resolution. |

The preview names each path, current state, proposed operation, source template
or rule, and whether approval is required. Unknown files are reported and
preserved; they are never implicitly skipped as if known or deleted. Directories,
symlinks, and parent-path containment must be checked before writes.

Apply the safe-regeneration guarantees established by
[`target-project-layout.md`](target-project-layout.md) and TASK-020:

- No write occurs during discovery, interview, summary review, or dry-run.
- An unapproved conflict blocks every write in the plan; there is no partial
  success before conflict resolution.
- A conflict overwrite requires explicit, single-use approval of the exact
  relative path. Approval for one path does not authorize another path, a
  directory replacement, deletion, or unrelated content.
- A permitted merge preserves user content and follows the exact merge
  semantics documented for that artifact. If preservation cannot be proved,
  classify as `CONFLICT`.
- Unknown files and unsupported manifests/versions are preserved.
- An unchanged rerun is idempotent and reports `SKIP` for unchanged managed
  files.
- The final manifest is sealed only after all approved writes and verification
  succeed. A partial failure reports exact completed/pending paths; do not
  disguise it as success or delete user work during rollback.

**Summary confirmation and write-plan approval are separate approvals.** The
user must approve the exact preview revision before operations execute. If
inventory or templates change after preview, recalculate and present a new
revision. Exact-path conflict approvals remain required even when the overall
plan is approved. Record approvals with user, date, exact scope/paths, and
evidence per the decision-and-approval protocol.

## 7. State flow, cancellation, and resumption

```text
PREFLIGHT → DISCOVER → INTERVIEW → SUMMARY_REVIEW → PLAN_PREVIEW
    → WRITE_PLAN_APPROVAL → GENERATION (future TASK-013) → VERIFY

DISCOVER / INTERVIEW / SUMMARY_REVIEW / PLAN_PREVIEW
    → PAUSED or CANCELLED
WRITE_PLAN_APPROVAL → PAUSED or CANCELLED
GENERATION → PARTIAL_FAILURE (report exact results; do not claim success)
```

- **Cancel:** stop immediately, perform no generation, preserve every existing
  path, and report collected answers and unresolved questions. Do not convert a
  cancelled intake into an initialized project.
- **Incomplete answers:** retain confirmed answers, label unanswered items
  unknown, and either continue if non-blocking or pause if they block the
  requested result. Never invent defaults to make the schema appear complete.
- **Pause/resume in the same available session:** resume from the last
  confirmed answer and pending-question list; recheck repository evidence before
  using it.
- **Resume after a session is lost:** do not assume conversational state is
  durable. Offer a concise initialization handoff containing the target path,
  confirmed answers, evidence paths, unknowns, pending questions, and summary
  revision. Persist it only if the user explicitly requests a path and approves
  the save plan; treat it as a draft, not canonical project state. On resume,
  re-read its sources and revalidate the target, versions, and collisions.
- **Stale or changed target:** discard stale inventory conclusions, rediscover
  affected paths, and require renewed summary/plan approval where the change
  affects scope or planned writes.
- **Already initialized target:** never start fresh over existing canonical
  state. Apply the existing version/reconciliation rules and require the
  separate approved upgrade path.

At every pause, cancellation, or error, report the current phase, completed
read-only work, pending decisions, and next safe action. The Orchestrator owns
all questions and state transitions.

## 8. Concrete acceptance scenarios

These scenarios define expected protocol behavior; they do not claim that a
generator has been implemented.

| ID | Starting state and evidence | User response / collision | Required observable result |
| --- | --- | --- | --- |
| INIT-S01 — greenfield | Empty directory; no stack manifests or `.blueprint/`. | User confirms purpose and scope but answers "unknown" for provider and deployment target. | Report greenfield; ask remaining required questions; list provider/deployment as unknown; do not infer them or write files before summary and plan approvals. |
| INIT-S02 — brownfield | Existing Git project with `pyproject.toml`, `src/`, `tests/`, `README.md`, and no `.blueprint/`. | Inventory proposes Python as a stack candidate with cited `pyproject.toml`; user corrects that this repository is archived and the active stack is unknown. | Record the observed marker and correction separately; ask/retain unknown active stack; do not claim Python is confirmed; continue only if the user confirms a coherent partial summary. |
| INIT-S03 — partial and resumable | Brownfield project; purpose and goals confirmed, data policy unanswered. | User pauses and asks to resume later. | Mark data policy unknown and blocking if the requested scope depends on it; make no writes; provide a draft handoff. Save it only to an explicitly approved path; on resume recheck evidence and target changes. |
| INIT-S04 — all preview outcomes | Confirmed summary; absent managed files, one identical file, one safely mergeable marked file, and one incompatible user-edited collision. | Preview yields `CREATE`, `SKIP`, `MERGE`, and `CONFLICT` respectively. | Show each path and diff; require plan approval for create/merge; conflict blocks all writes. After a revised preview, overwrite only if the exact conflicting path receives explicit single-use approval. |
| INIT-S05 — summary is not write approval | Brownfield project with only absent destinations. | User confirms summary but has not approved the preview. | Remain at plan approval; do not write `CREATE` operations. |
| INIT-S06 — existing Blueprint needs reconciliation | `.blueprint/` exists but `manifest.json` is missing, invalid, or version is unsupported. | User requests a fresh install. | Report exact missing/invalid/unsupported state; stop before writes; do not treat it as greenfield or overwrite canonical records. |
| INIT-S07 — cancel during interview | Empty directory; no answers beyond purpose. | User cancels. | Stop, leave the target unchanged, report the partial answer and unanswered questions, and do not create tasks or files. |
| INIT-S08 — purpose field mapping | Greenfield project; the user gives one sentence describing the project's purpose. | User confirms using the sentence for both required fields, or explicitly requests distinct description and purpose values. | Use the confirmed sentence verbatim for both `project.description` and `purpose.summary` by default; when distinct values are requested, ask and confirm both separately. Never infer either value. |
| INIT-S09 — initialization status | Required scalar fields are confirmed; one provider preference remains unknown but does not block the approved scope. | User approves a partial initialization. Later, the provider is confirmed. | Persist `partial` with the provider unknown retained. Once all unknowns are resolved and the revised summary and plan are approved, persist `complete` with an empty unknowns array. Any blocking unknown prevents writes. |

### Acceptance-criterion mapping

| TASK-012 criterion | Specification evidence |
| --- | --- |
| Existing and empty project flows are covered. | §§3, 3.1, 8 (INIT-S01, INIT-S02, INIT-S06). |
| Unknowns are explicit, not fabricated. | §§2, 4, 5, 7, 8 (INIT-S01–S03, INIT-S08–S09). |
| User confirms summary before generation. | §§1, 5, 6, 8 (INIT-S04, INIT-S05). |
| Collision preview is part of the flow. | §6 and §8 (INIT-S04). |

## 9. Scope boundary and follow-up

This contract does not implement interactive file discovery, question
rendering, migrations, or validation commands. TASK-013 implements generation
and collision execution from Orchestrator-confirmed input; TASK-014 owns
schema and task-graph validation. This document remains the normative source
for initialization inputs, approval gates, states, and expected outcomes. No
monitor behavior is changed.
