# Current State

- Date: 2026-11-04
- Stage: core contracts defined; moving through the approved task dependency graph.
- Repository: `jsalinasanzules/developer-ai-init`, public, default branch `main`.
- Personal GitHub read/write access verified.
- The foundation, nine specifications, eighteen task briefs, memory records, templates, and registry are committed.
- TASK-001 review: `docs/reviews/2026-11-04-task-001-foundation-review.md`.
- TASK-002 target-project layout: `docs/architecture/target-project-layout.md`.
- TASK-003 schemas: `schemas/README.md` and `schemas/*.schema.json`.
- TASK-004 memory protocol: `docs/architecture/memory-protocol.md`.
- TASK-005 decision protocol: `docs/architecture/decision-and-approval-protocol.md`.
- TASK-006 task lifecycle: `docs/architecture/task-lifecycle.md`.
- TASK-007 memory consolidation: `docs/architecture/memory-consolidation.md`.
- TASK-008 role contracts: `docs/architecture/agent-hierarchy.md` and `prompts/`.

## Active task
**TASK-009 — Implement OpenCode adapter using verified current conventions**
- Status: ready; dependencies TASK-002 and TASK-008 are done.
- Specs: SPEC-006, SPEC-007.
- Next action: revalidate official OpenCode V2 documentation and implement the adapter mapping.

## Completed recently
- **TASK-001** (`done`): foundation review and OpenCode capability validation.
- **TASK-002** (`done`): canonical `.blueprint/` tree, file catalog, ownership, collision, and upgrade policies.
- **TASK-003** (`done`): versioned JSON schemas, fixtures, and cross-reference rules; 15/15 fixture expectations pass.
- **TASK-004** (`done`): deterministic startup read protocol, context packet, ownership map, write triggers, and compaction rules.
- **TASK-005** (`done`): conflict classification, approval packet, attribution, expiry, and decision supersession.
- **TASK-006** (`done`): task schema, transition matrix, dependency validation, evidence mapping, and cold-start handoff format.
- **TASK-007** (`done`): memory proposal lifecycle, ownership/provenance, semantic merge, and concurrent-edit safeguards; scenario checks pass.
- **TASK-008** (`done`): role contracts, delegation/review payloads, escalation, sequential fallback, and provider-neutral prompt templates.

## Approved decisions
- **ADR-006:** V2-native OpenCode adapter baseline, with portable Markdown commands/skills where practical.
- **ADR-007:** opt-in depth-2 delegation (`experimental.subagent_depth: 2`) with sequential fallback.
- **ADR-008:** provider-neutral observability contract in the Blueprint core; optional provider-specific monitor UI. The first monitor is an OpenCode TUI sidebar plugin owned by this Blueprint and installed into generated projects.
- Pending future decision: initializer/validator implementation stack (needed before TASK-012/TASK-013).

## Verified constraints
- No mandatory database, hosted service, or network dependency.
- Canonical memory remains provider-independent and Git-native.
- Do not implement every phase automatically; follow task dependencies.
- Ask about conflicts and material decisions.
- Done requires observable verification evidence.
- OpenCode 1 and OpenCode 2 share the `opencode` command; this environment runs `v2.2.5`.
- OpenCode's default subagent depth is `1`; true Orchestrator → Manager → Specialist delegation requires depth `2` (experimental in V2) or the documented fallback.

## Planned observability work
- **TASK-019** (`proposed`): define the provider-neutral observability contract and OpenCode monitor. Dependencies: TASK-002, TASK-006, TASK-008. See `tasks/items/TASK-019.md`.

## Blockers
None recorded.

## Next
Start TASK-009 (dependencies TASK-002 and TASK-008 are done). Revalidate OpenCode V2 docs before implementing the adapter.
