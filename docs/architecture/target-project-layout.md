# Target-Project Blueprint Layout and Ownership

- Status: accepted design baseline for TASK-002
- Date: 2026-11-04
- Specs: SPEC-001, SPEC-002
- Related decisions: ADR-001, ADR-002, ADR-006, ADR-007

## 1. Purpose

This document defines the canonical `.blueprint/` directory installed into a target project, the purpose and ownership of every file, which records are authoritative, and how initialization and upgrades avoid destroying user work.

It applies to initialized projects. It does **not** describe this repository's own development memory at root `/memory`.

## 2. Design rules

1. `.blueprint/` is the canonical project-owned knowledge store. It is committed to Git.
2. Baseline operation uses local files and Git only. No database, hosted service, or network call is required.
3. Provider-specific configuration lives outside `.blueprint/` and is generated or merged by an adapter.
4. `registry.json` is authoritative for machine-readable task status; task Markdown files are authoritative for task scope, acceptance criteria, and evidence.
5. Append-only records (`DECISIONS.md`, sessions, handoffs) are not rewritten to hide history.
6. Every file is classified as canonical, blueprint-managed, provider-native, derived, or ephemeral.
7. Initialization and upgrades detect collisions, preview changes, and never overwrite user content without explicit approval.
8. Unknown files and unknown blueprint versions are preserved and reported, never guessed or deleted.
9. No secrets, credentials, tokens, or unnecessary sensitive personal data are stored.

10. Internal Blueprint tooling does not impose its implementation runtime on generated target projects.

## 3. Canonical tree

```text
<project-root>/
├── .blueprint/
│   ├── README.md
│   ├── manifest.json
│   ├── config/
│   │   ├── project.json
│   │   └── agents.json
│   ├── schemas/
│   │   ├── manifest.schema.json
│   │   ├── project.schema.json
│   │   ├── agents.schema.json
│   │   ├── memory-metadata.schema.json
│   │   └── task-registry.schema.json
│   ├── memory/
│   │   ├── PROJECT_CONTEXT.md
│   │   ├── CURRENT_STATE.md
│   │   ├── ARCHITECTURE.md
│   │   ├── DECISIONS.md
│   │   ├── CONVENTIONS.md
│   │   └── metadata.json
│   ├── specs/
│   │   ├── README.md
│   │   └── SPEC-<NNN>-<slug>.md
│   ├── tasks/
│   │   ├── registry.json
│   │   ├── backlog.md
│   │   ├── TASK-TEMPLATE.md
│   │   └── items/
│   │       ├── README.md
│   │       └── TASK-<NNN>.md
│   ├── sessions/
│   │   ├── README.md
│   │   ├── SESSION-TEMPLATE.md
│   │   └── YYYY-MM-DD-<slug>.md
│   ├── handoffs/
│   │   ├── README.md
│   │   ├── HANDOFF-TEMPLATE.md
│   │   └── YYYY-MM-DD-<slug>.md
│   └── derived/                         # optional, gitignored, rebuildable
│       └── <indexes, caches, local reports>
└── <provider-native files: AGENTS.md, opencode.jsonc, .opencode/, etc.>
```

The exact JSON field sets are defined by the schemas produced in TASK-003. The tree and ownership rules in this document remain authoritative for where files live and who may write them.

## 4. File catalog

Classification:

- **C — Canonical:** project-owned knowledge; committed to Git; authoritative for its subject.
- **B — Blueprint-managed:** supplied or replaced by the blueprint; committed to Git; changes are detected against `manifest.json`.
- **P — Provider-native:** adapter-generated outside `.blueprint/`; never the sole source of project knowledge.
- **D — Derived:** optional, rebuildable, excluded from Git.
- **E — Ephemeral:** conversation or process state; never the only copy of durable knowledge.

| Path | Class | Purpose | Writer / owner | Write events | Source of truth for |
| --- | --- | --- | --- | --- | --- |
| `.blueprint/README.md` | C | Entry point: project identity, startup order, blueprint version, navigation. | Orchestrator; user may approve edits | Initialization; navigation or startup changes | Startup order and project-level navigation |
| `.blueprint/manifest.json` | B | Installed blueprint version, schema version, install timestamp, file inventory with install-time hashes. | Initializer/upgrader only | Successful initialization or approved upgrade | Installed blueprint/schema version and collision baseline |
| `.blueprint/config/project.json` | C | Machine-readable project facts: identity, purpose, users, goals, scope, constraints, stack, unknowns, assumptions, provider preferences. | Orchestrator after user confirmation | Initialization; approved project-fact changes | Project facts and initialization completeness |
| `.blueprint/config/agents.json` | C | Project role configuration: Orchestrator, managers, specialists, delegation mode, approval policy, adapter references. | Orchestrator after user confirmation | Role or delegation-policy change; adapter selection | Project role configuration |
| `.blueprint/schemas/*.schema.json` | B | Versioned JSON Schemas for manifest, project config, agents config, memory metadata, and task registry. | Blueprint distribution; replaced only on approved upgrade | Initialization or upgrade | Validation shape, not project content |
| `.blueprint/memory/PROJECT_CONTEXT.md` | C | Durable purpose, users, goals, scope, domain vocabulary, constraints, non-goals. | Orchestrator; user approves material changes | Initialization; durable context change | Project context |
| `.blueprint/memory/CURRENT_STATE.md` | C | Concise snapshot: active task, status, blockers, next action, pending approvals. | Orchestrator | Task transition; blocker; meaningful progress; session close | Current operational state |
| `.blueprint/memory/ARCHITECTURE.md` | C | Current architecture, boundaries, components, data ownership, important constraints. | Orchestrator after architecture approval | Approved architecture change | Current architecture |
| `.blueprint/memory/DECISIONS.md` | C | Append-only decision records with context, options, choice, rationale, consequences, date, status, supersession. | Orchestrator | Approved material decision; supersession | Decision history |
| `.blueprint/memory/CONVENTIONS.md` | C | Coding, testing, documentation, branching, review, and operational conventions. | Orchestrator | Approved convention change | Development conventions |
| `.blueprint/memory/metadata.json` | C | Machine-readable record pointers, owning roles, last update timestamps, schema version, optional derived-index pointers. | Orchestrator or memory steward | Record update; consolidation | Memory record metadata |
| `.blueprint/specs/README.md` | C | Specification index and specification conventions. | Orchestrator | New or renamed specification | Specification navigation |
| `.blueprint/specs/SPEC-<NNN>-<slug>.md` | C | Normative project requirements, acceptance criteria, dependencies, open questions. | Orchestrator; managers propose | New specification; approved requirement change | Normative requirements |
| `.blueprint/tasks/registry.json` | C | Machine-readable task status, priority, owner role, spec links, dependencies, next action. | Orchestrator | Task creation or status transition | Task status and dependency graph |
| `.blueprint/tasks/backlog.md` | C (projection) | Human-readable roadmap grouped by phase; synchronized with `registry.json`. | Orchestrator | Task creation or status transition | Nothing independently; if it conflicts with `registry.json`, registry wins and the backlog must be corrected |
| `.blueprint/tasks/TASK-TEMPLATE.md` | B | Default task brief structure. Projects may customize it. | Blueprint distribution; project may edit with approval | Initialization; approved template customization | Expected task-brief fields |
| `.blueprint/tasks/items/README.md` | B | Explains task-item conventions. | Blueprint distribution | Initialization or upgrade | Task-item conventions |
| `.blueprint/tasks/items/TASK-<NNN>.md` | C | Detailed task objective, scope, exclusions, acceptance criteria, verification, evidence, blockers. | Orchestrator; specialists propose | Task creation; scope/evidence update; transition | Task scope, acceptance criteria, and evidence |
| `.blueprint/sessions/README.md` | B | Explains session-summary purpose and naming. | Blueprint distribution | Initialization or upgrade | Session-record conventions |
| `.blueprint/sessions/SESSION-TEMPLATE.md` | B | Default concise session-summary structure. | Blueprint distribution; project may edit with approval | Initialization; approved customization | Expected session fields |
| `.blueprint/sessions/YYYY-MM-DD-<slug>.md` | C | Append-only session summary: work, evidence, decisions, next action. | Orchestrator | End of a meaningful session | Session history |
| `.blueprint/handoffs/README.md` | B | Explains handoff purpose and naming. | Blueprint distribution | Initialization or upgrade | Handoff conventions |
| `.blueprint/handoffs/HANDOFF-TEMPLATE.md` | B | Default handoff structure for cross-session or cross-provider continuation. | Blueprint distribution; project may edit with approval | Initialization; approved customization | Expected handoff fields |
| `.blueprint/handoffs/YYYY-MM-DD-<slug>.md` | C | Append-only handoff: repository state, completed work, evidence, risks, decisions, next action. | Orchestrator | Task or session handoff | Continuation record |
| `.blueprint/derived/**` | D | Optional indexes, embeddings, caches, or local reports. Must be reproducible from canonical files. | Any local tool | Rebuild; refresh | Nothing authoritative |

## 5. Ownership model

### 5.1 Authority

`USER → ORCHESTRATOR → MANAGERS → SPECIALISTS`

- **User:** owns product intent, priorities, and approval of material decisions. The user may edit any file but should route durable changes through the Orchestrator so records stay consistent.
- **Orchestrator:** sole writer/consolidator of shared canonical records and sole user-facing role.
- **Managers:** coordinate a domain, review specialist output, and propose changes to specs, tasks, architecture, and conventions.
- **Specialists:** execute bounded work and return evidence plus proposed memory updates. They do not overwrite shared canonical records directly.
- **Initializer/upgrader:** writes `B` files and initial `C` files only during initialization or an approved upgrade. It must not overwrite user-modified content.
- **Adapters:** generate or merge `P` files outside `.blueprint/`. They must reference, not replace, canonical records.
- **Local tools:** may write `D` files. They must not write canonical records unless acting through an approved Orchestrator workflow.

### 5.2 Write discipline

- Write each durable fact to its owning record; do not duplicate it across records.
- Update `CURRENT_STATE.md` after task transitions, blockers, and meaningful progress.
- Update `registry.json` and the task item together; reconcile any conflict instead of silently choosing a side.
- Append decisions and supersession links; never erase decision history.
- Record verification evidence for every completed acceptance criterion.
- Specialists return proposed changes; the Orchestrator reviews and consolidates them.
- No record may contain credentials, tokens, private keys, or unnecessary sensitive data.

## 6. Root development memory vs target-project memory

| Concern | This repository (blueprint source) | Initialized target project |
| --- | --- | --- |
| Canonical memory | `/memory/` | `.blueprint/memory/` |
| Task records | `/tasks/` | `.blueprint/tasks/` |
| Specifications | `/specs/` | `.blueprint/specs/` |
| Session records | `/sessions/` | `.blueprint/sessions/` |
| Handoffs | `/handoffs/` | `.blueprint/handoffs/` |
| Architecture docs | `/docs/architecture/` | `.blueprint/memory/ARCHITECTURE.md` plus project docs |
| Agent instructions | root `AGENTS.md` (blueprint development) | adapter-generated root `AGENTS.md` (target project) |

Rules:

- Root memory records the development of the blueprint itself. It is never copied into a target project as that project's history.
- Target-project memory starts from templates and the initialization interview, not from this repository's decisions or tasks.
- A target project's `.blueprint/` must not reference this repository's development memory as if it were project knowledge.
- This repository does not initialize itself as a target project; doing so would mix the two scopes.

## 7. Initialization and collision policy

Initialization is a preflight, approval, and write sequence:

1. **Inspect:** detect whether the target is new or existing; detect `.git`, `.blueprint/`, `AGENTS.md`, `CLAUDE.md`, `opencode.json(c)`, `.opencode/`, and other adapter paths.
2. **Classify:** mark each planned path as `absent`, `identical`, `user-modified`, `unknown`, or `conflict`.
3. **Plan:** produce a preview of `create`, `skip`, `merge`, or `stop` actions. Never plan a silent overwrite or deletion.
4. **Approve:** show the plan and require explicit approval for merges, replacements, and any change to existing user content.
5. **Write:** write only approved paths. Prefer temporary file plus atomic rename. Do not remove unknown files.
6. **Verify:** validate JSON, links, task graph, and ownership metadata. Report warnings separately from blocking errors.
7. **Seal:** write `manifest.json` last, after all approved files succeed, recording versions and install-time hashes.

Collision rules:

- `absent` → create.
- `identical` → skip.
- `user-modified` → preserve; show diff; require explicit per-file approval before merge or replacement.
- `unknown` → preserve and report; never delete or reinterpret.
- `conflict` (same path, incompatible semantics) → stop and ask the user.
- Re-running initialization must be idempotent: no changes when the target is already current and unmodified.
- Partial failure must be reported with the exact completed and pending actions; do not attempt destructive rollback.

## 8. Upgrade policy

`manifest.json` records `blueprint_version`, `schema_version`, and install-time hashes.

1. Read and validate the manifest. Missing or invalid manifest → stop and ask; do not guess the installed version.
2. If the installed version is newer than the tool, or unknown → stop and report.
3. If versions match → no upgrade is needed; report current state.
4. If an upgrade is available → generate a migration plan from documented version-to-version migrations.
5. Compare each blueprint-managed file's current hash with its install-time hash:
   - **unmodified:** eligible for replacement, still shown in the plan;
   - **user-modified:** preserve, show a diff, and require explicit approval per file;
   - **missing:** offer recreation only with approval;
   - **unknown path:** preserve and report.
6. Canonical project data is migrated only through documented, reviewed migrations. If a migration is not reversible, require approval and record it in `DECISIONS.md`.
7. Never require network access or a database for the baseline upgrade.
8. After success, rewrite `manifest.json` and record the upgrade in `CURRENT_STATE.md`; record material changes in `DECISIONS.md`.

Provider-native upgrade behavior is adapter-specific and is defined and tested in TASK-009/TASK-011. It must follow the same detect-preview-approve rules.

## 9. Optional and derived data

- `.blueprint/derived/` is optional and excluded from Git. It may contain indexes, embeddings, caches, or generated reports.
- Deleting `.blueprint/derived/` must never remove canonical knowledge.
- Any derived artifact must be reproducible from canonical records and documented enough to rebuild.
- A project with no derived directory is fully functional.

## 10. Acceptance evidence for TASK-002

| Criterion | Evidence |
| --- | --- |
| Canonical tree documented | §3 |
| Each file has purpose, owner, write events, and source-of-truth status | §4 |
| Root development memory distinguished from target memory | §6 |
| Collision and upgrade policies defined | §7 and §8 |
| No mandatory database or service introduced | §2, §8, §9 |
