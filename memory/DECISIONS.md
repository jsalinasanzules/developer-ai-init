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

## ADR-006 — OpenCode V2-native adapter baseline
- Status: accepted | Date: 2026-11-04
- Context: OpenCode V2 is current (`v2.2.5` observed locally); V1 and V2 use different native config shapes, while V2 reads supported V1 configuration.
- Decision: the first adapter generates V2-native agents, commands, skills, and configuration; portable Markdown commands/skills are preferred where practical; V1 limitations are documented rather than claimed as conformance.
- Rationale: aligns with the current provider version, avoids deprecated V1 frontmatter, and preserves a documented migration path.
- Consequence: V2-native permission/agent files are not V1-compatible; adapter conformance claims are explicitly V2-scoped. TASK-009 must revalidate current official documentation before implementation.

## ADR-007 — Opt-in depth-2 hierarchy with sequential fallback
- Status: accepted | Date: 2026-11-04
- Context: OpenCode defaults `subagent_depth` to 1, which prevents a Manager subagent from launching Specialist subagents. V2 exposes depth 2 under `experimental.subagent_depth`.
- Decision: the adapter may enable depth 2 when the user approves it, documents it as an experimental provider dependency, and provides a sequential single-agent fallback when unavailable.
- Rationale: preserves Managers as real coordinators/reviewers without making true nesting mandatory for baseline operation.
- Consequence: adapter conformance must cover both depth-2 (when enabled) and sequential fallback; experimental behavior may change.
