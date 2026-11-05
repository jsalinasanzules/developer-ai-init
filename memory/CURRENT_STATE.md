# Current State

- Date: 2026-11-05
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
- TASK-009 OpenCode adapter: `adapters/opencode/` (templates, manifest, conformance report).

## Active task
**TASK-012 — Specify project discovery and interactive initialization**
- Status: `ready`; dependencies TASK-001 and TASK-002 are `done`. User approved
  the proposal on 2026-11-05; no implementation began in the TASK-020 recovery.

## Completed recently
- **TASK-010** (`done`): live cold-start, task-selection, evidence-backed lifecycle (TASK-900 four-transition history `06bdd19`/`1d53129`/`9795b73`/`2bad731`), and handoff production/consumption verified against Crouton Alpha; report `docs/reviews/2026-11-04-task-010-verification.md`.
- **TASK-011** (`done`, historical): acceptance audit found its monitor presentation work did not implement safe regeneration or behavioral conformance; correction tracked by TASK-020.
- **TASK-001** (`done`): foundation review and OpenCode capability validation.
- **TASK-002** (`done`): canonical `.blueprint/` tree, file catalog, ownership, collision, and upgrade policies.
- **TASK-003** (`done`): versioned JSON schemas, fixtures, and cross-reference rules; 15/15 fixture expectations pass.
- **TASK-004** (`done`): deterministic startup read protocol, context packet, ownership map, write triggers, and compaction rules.
- **TASK-005** (`done`): conflict classification, approval packet, attribution, expiry, and decision supersession.
- **TASK-006** (`done`): task schema, transition matrix, dependency validation, evidence mapping, and cold-start handoff format.
- **TASK-007** (`done`): memory proposal lifecycle, ownership/provenance, semantic merge, and concurrent-edit safeguards; scenario checks pass.
- **TASK-008** (`done`): role contracts, delegation/review payloads, escalation, sequential fallback, and provider-neutral prompt templates.
- **TASK-009** (`done`): OpenCode V2 adapter templates (agents, commands, config, AGENTS.md), role mapping, collision policy, and conformance report; smoke-tested against OpenCode 2.2.5.
- **TASK-019** (`done`): provider-neutral observability contract and OpenCode monitor; 23/23 snapshot checks pass, user confirmed monitor load, `/monitor` sidebar toggle, and reload after restart in OpenCode 2.2.5; storage proxy fix committed as `bdfbce1`.
- **TASK-020** (`done`): evidence gate approved the acceptance evidence and synchronized task records; Manager review `docs/reviews/2026-11-05-task-020-gate-review.md`.

## Approved decisions
- **ADR-006:** V2-native OpenCode adapter baseline, with portable Markdown commands/skills where practical.
- **ADR-007:** opt-in depth-2 delegation (`experimental.subagent_depth: 2`) with sequential fallback.
- **ADR-008:** provider-neutral observability contract in the Blueprint core; optional provider-specific monitor UI. The first monitor is an OpenCode TUI sidebar plugin owned by this Blueprint and installed into generated projects.
- **ADR-009:** Python 3.9+ standard-library tooling is source-repository-only; generated target projects acquire no Python runtime dependency from Blueprint tooling.
- Pending future decision: initializer/validator implementation stack (needed before TASK-012/TASK-013).

## Verified constraints
- No mandatory database, hosted service, or network dependency.
- Canonical memory remains provider-independent and Git-native.
- Internal Python tools are permitted, but generated target projects must remain free of Python runtime requirements unless separately approved.
- Do not implement every phase automatically; follow task dependencies.
- Ask about conflicts and material decisions.
- Done requires observable verification evidence.
- OpenCode 1 and OpenCode 2 share the `opencode` command; this environment runs `v2.2.5`.
- OpenCode's default subagent depth is `1`; true Orchestrator → Manager → Specialist delegation requires depth `2` (experimental in V2) or the documented fallback.

## Observability work
TASK-019 is complete: `docs/architecture/observability.md` v1.0.0 and one reusable OpenCode monitor implementation at `adapters/opencode/monitor/` serve both canonical contexts (`.blueprint/` and the development layout). Verification includes 23/23 snapshot checks, OpenCode 2.2.5 plugin-load evidence, and user-confirmed sidebar visibility toggle and reload after restart.

## Blockers
None. TASK-020 is complete. TASK-010's historical free-model-limit blocker was resolved by Crouton Alpha live verification; see `tasks/items/TASK-010.md`.

## Pending approvals
None for TASK-012. The initializer/validator implementation-stack decision
remains a future approval gate before implementation work, not before this
specification task.

## Next
Begin TASK-012 only when execution is started; transition it to `in_progress`
before doing specification work.
