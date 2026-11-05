# TASK-019 — Define provider-neutral observability contract and OpenCode monitor

## Metadata
- Status: in_review
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-006, SPEC-007
- Dependencies: TASK-002, TASK-006, TASK-008
- Created: 2026-11-04
- Updated: 2026-11-05

## Objective
Define a provider-neutral observability contract for Blueprint execution and specify the first provider-specific presentation, `developer-ai-init-monitor`, as an OpenCode TUI sidebar plugin.

## Context
ADR-008 establishes that observability semantics and canonical state belong to the Blueprint core, while provider-specific monitor UIs belong to adapters. The monitor source is owned/versioned in this Blueprint repository, installed by the initializer into generated projects, and reads canonical state from the generated project's `.blueprint/` directory. The monitor is optional and must never become a second source of truth.

## Scope
- Define the core observability data model for task state, active execution, role/agent assignments, progress evidence, blockers, approval requests, handoffs, and update timestamps.
- Define data ownership, event/update semantics, freshness indicators, and consistency expectations.
- Define provider-neutral interfaces/contracts consumed by provider adapters.
- Specify the OpenCode monitor's responsibilities, plugin packaging/discovery, TUI sidebar integration, and supported-version compatibility checks.
- Define degraded/manual behavior when live OpenCode events or sidebar capabilities are unavailable.
- Define installation, configuration, versioning, collision detection, and safe upgrade expectations.
- Establish a minimal compatibility spike and verification plan for OpenCode 2.2.5 before committing to implementation details.

## Out of scope
- Implementing the full OpenCode plugin UI.
- Modifying OpenCode itself.
- Making a hosted monitoring service, database, or network connection mandatory.
- Duplicating canonical task, approval, agent, or handoff state inside the plugin.
- Implementing Claude Code or Cursor monitor UIs.

## Acceptance criteria
- [x] A provider-neutral observability contract and data ownership model are documented (`docs/architecture/observability.md` v1.0.0 §2, §4, §5).
- [x] Required fields and lifecycle/update semantics are defined for tasks, agents, blockers, approvals, and handoffs (contract §4, §6).
- [x] OpenCode TUI plugin architecture and sidebar integration are verified against official documentation and a minimal compatibility spike for v2.2.5 (plugin load + `stage=setup` proven in 2.2.5 debug logs; caveat: interactive sidebar visual render confirmed via docs + load evidence, pending user visual confirmation).
- [x] Installation and upgrade behavior is optional, reproducible, versioned, and non-destructive (`adapters/opencode/monitor/README.md` §Install; plugin v0.1.0).
- [x] A degraded mode displays last persisted state and its freshness when live updates are unavailable (contract §8; verified by snapshot tests incl. uninitialized and unparsable-record cases).
- [x] Core workflows remain fully usable with the monitor disabled or unavailable (monitor is independent and optional; TASK-009 smoke ran adapter commands without it).

## Verification plan
- Review the contract against existing task, memory, decision, and handoff schemas.
- Validate all referenced fields against the current schemas or propose explicit schema changes.
- Run a minimal OpenCode 2.2.5 plugin spike to verify discovery, TUI entrypoint, sidebar slot, and update behavior.
- Test that the monitor reads canonical files and does not mutate authoritative state.
- Review safe installation behavior against existing `.opencode/` user configuration.

## Risks and open questions
- OpenCode plugin/TUI APIs may change between releases; pin and document the verified compatibility range.
- The exact split between persisted snapshots and live provider events must be explicit.
- Avoid coupling the core schema to OpenCode-specific session or event identifiers.

## Blockers
None.

## Execution log
- 2026-11-04: Created after user approval of ADR-008.
- 2026-11-04: Verified spec/docs/backlog and the OpenCode V2 plugin API (server + TUI parts, `sidebar.content` slot) against official v2 docs pages.
- 2026-11-04/05: Implemented `adapters/opencode/monitor/` (shared read-only reader `src/blueprint.ts`, server part `src/index.ts`, TUI part `src/tui.tsx`, README) as ONE implementation serving both canonical contexts: `.blueprint/` (generated projects) and the root development layout (this repo), via nearest-canonical-root resolution.
- 2026-11-05: Wrote contract doc `docs/architecture/observability.md` v1.0.0 (snapshot model, ownership map, update/degraded semantics, evidence table).
- 2026-11-05: `bun run scripts/verify-observability-snapshot.ts` → RESULT: PASS (23/23) — Context A (dev layout: 19 tasks, active TASK-019, 8 ADRs, latest ADR-008), Context B (`.blueprint/` fixture: selection, evidence counts 2/3, blockers/approvals, project slug, handoff listing with template exclusion), Context D (uninitialized degraded), and a no-write proof. Fixed one reader bug found during testing (project slug must read `project_id`).
- 2026-11-05: Built spike project at `/private/var/folders/pg/sdm_xthn0rbgcgyzlrmhhj800000gn/T/opencode/task019-spike` with the monitor installed under `.opencode/plugins/developer-ai-init-monitor/` and a seeded `.blueprint/`. On OpenCode v2.2.5: TUI started and exited cleanly; with `--standalone --log-level debug --print-logs`, debug output proves full plugin load — server part `msg="loading plugin" id=…/developer-ai-init-monitor entrypoint=…/src/index.ts` + watcher subscribe, TUI part `stage=read` on `src/tui.tsx` then `stage=setup plugin=developer-ai-init-monitor` completed; no monitor/plugin errors.
- 2026-11-05: Attempted headless pty capture of the sidebar visual render (multiple sizes/methods); TUI renders but sidebar slot text was not captured in any headless attempt (`/tmp/oc-tui3.log`, 0 matches for "Blueprint"). Interactive visual confirmation deferred to the user.
- 2026-11-05: Status set to `in_review` per memory-protocol rule: every criterion has logged evidence, with the explicit sidebar-render caveat; final `done` awaits the user's interactive confirmation of the sidebar + `/monitor` toggle in the spike project.

## Completion evidence

| Criterion | Evidence |
| --- | --- |
| Provider-neutral contract + ownership | `docs/architecture/observability.md` v1.0.0 (§2 principles, §4 snapshot model, §5 ownership/prohibition map). |
| Fields & lifecycle/update semantics | contract §4 (snapshot fields) and §6 (refresh triggers, mtime poll ≤1 Hz, consistency, partial reads, caching, security). |
| OpenCode v2.2.5 compatibility spike | Spike project + debug logs (see `docs/architecture/monitor-spike-2026-11-04.md`): plugin fully loads and initializes on v2.2.5; `/monitor` command and `sidebar.content` slot per official v2 docs (`/v2/docs/build/plugins/cli`). Caveat: headless pty could not capture the sidebar visually; interactive render pending user confirmation. |
| Optional, safe installation | `adapters/opencode/monitor/README.md` §Install; plugin not installed by default flows; works from `.opencode/plugins/` discovery only; version 0.1.0. |
| Degraded mode | Snapshot test Context D (uninitialized) + unparsable-record `issues` paths; stale labeling via `freshness` + `read_at`. |
| Workflows usable with monitor off | Monitor is an independent plugin; TASK-009's live `/blueprint-next` smoke ran in a project without the monitor. |
| One reusable implementation for both contexts | Same reader verified against Context A (this repo) and Context B (`.blueprint/` fixture); 23/23 PASS; no duplicated canonical state (no-write proof included). |

## Next action
Await user interactive confirmation of the sidebar render + `/monitor` toggle in the spike project (`cd /private/var/folders/pg/sdm_xthn0rbgcgyzlrmhhj800000gn/T/opencode/task019-spike && opencode`), then set status `done`.
