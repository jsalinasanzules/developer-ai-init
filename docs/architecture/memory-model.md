# Persistent Memory Model

## Goals
Preserve project continuity across sessions, models, and providers while keeping memory inspectable, editable, versionable, and independent of external services.

## Canonical target-project layout
The authoritative tree, file catalog, ownership, and collision/upgrade rules are defined in [Target-Project Blueprint Layout and Ownership](target-project-layout.md). A summary:

```text
.blueprint/
├── README.md
├── manifest.json
├── config/
│   ├── project.json
│   └── agents.json
├── schemas/
│   └── *.schema.json
├── memory/
│   ├── PROJECT_CONTEXT.md
│   ├── CURRENT_STATE.md
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── CONVENTIONS.md
│   └── metadata.json
├── specs/
├── tasks/
│   ├── registry.json
│   ├── backlog.md
│   ├── TASK-TEMPLATE.md
│   └── items/
├── sessions/
│   └── SESSION-TEMPLATE.md
├── handoffs/
│   └── HANDOFF-TEMPLATE.md
└── derived/            # optional, gitignored, rebuildable
```

Provider configuration (for example OpenCode agent definitions) is generated separately and linked to the canonical project roles.

## Memory records and ownership
- `PROJECT_CONTEXT.md`: purpose, users, goals, scope, domain vocabulary, constraints.
- `CURRENT_STATE.md`: concise current snapshot, active work, known blockers, next actions.
- `ARCHITECTURE.md`: current architecture and important boundaries.
- `DECISIONS.md`: append-only decision records, including supersession.
- `CONVENTIONS.md`: coding, testing, branching, documentation, and operational conventions.
- `metadata.json`: schema version, update metadata, and optional record pointers; never secrets.

## Read protocol
At session start, read the blueprint README, project context, current state, task registry, active task, linked specification, and relevant decisions/conventions. Expand context only as needed. Never assume conversation history is available. The deterministic read order, active-task selection, failure handling, and startup context packet are defined in [Memory Read/Write Protocol and Startup Context Packet](memory-protocol.md).

## Write protocol
Write durable facts to their owning record. Update current state when active work or blockers change. Record material approved choices in decisions. Update task registry on transitions. Append concise session summaries and create handoffs when work crosses sessions. The event table, ownership map, non-write cases, and compaction rules are defined in [Memory Read/Write Protocol and Startup Context Packet](memory-protocol.md).

## Consolidation and concurrency
Specialists submit proposed updates with source/evidence. The Orchestrator or designated memory steward reviews and consolidates them. Concurrent edits to shared records require semantic reconciliation; never use last-write-wins for decisions or task state. The full proposal lifecycle, provenance model, and conflict reconciliation procedure are in [Memory Consolidation and Concurrent Update Safeguards](memory-consolidation.md).

## Privacy and integrity
Never store credentials, access tokens, private keys, or secrets. Avoid unnecessary personal or sensitive information. Missing or contradictory records must be surfaced for resolution. Derived indexes must be reproducible from canonical files.
