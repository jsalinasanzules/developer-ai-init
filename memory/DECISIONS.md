# Decision Log

Append new decisions. Do not erase history; mark replaced decisions superseded and link the replacement.

## ADR-001 — Git-native canonical memory
- Status: accepted | Date: 2026-11-04
- Context: memory must survive provider/session changes and remain portable.
- Decision: project-owned Markdown/JSON committed with the project is canonical.
- Rationale: inspectable, editable, diffable, portable, no hosted dependency.
- Consequence: explicit read/write protocols; indexes are derived and rebuildable.

## ADR-002 — No mandatory database
- Status: accepted | Date: 2026-11-04
- Decision: PostgreSQL/Supabase/vector database is not required for baseline memory.
- Consequence: file schemas and local validation are required; optional retrieval may be added later.

## ADR-003 — Hierarchical authority
- Status: accepted | Date: 2026-11-04
- Decision: USER → ORCHESTRATOR → MANAGERS → SPECIALISTS; Orchestrator alone faces the user.
- Consequence: adapters preserve role boundaries or document sequential fallback.

## ADR-004 — OpenCode first, provider-neutral core
- Status: accepted | Date: 2026-11-04
- Decision: implement OpenCode first behind a provider adapter contract.
- Consequence: verify current official conventions; later adapters may include Claude Code and Cursor.

## ADR-005 — Approval for conflicts and material decisions
- Status: accepted | Date: 2026-11-04
- Decision: Orchestrator pauses for user approval before resolving material conflicts or consequential actions.
- Consequence: explicit conflict/approval workflow and decision records are required.
