# Product Backlog

The machine-readable source of task status is `registry.json`. Keep this view synchronized.

## Phase 0 — Foundation
- [x] **TASK-001** (done, critical): Review foundation and approve core architecture. No dependencies.
- [x] **TASK-002** (done): Finalize target-project blueprint directory and file ownership. Depends on TASK-001.
- [x] **TASK-003** (done): Define JSON schemas. Depends on TASK-002.

## Phase 1 — Persistent memory and task continuity
- [x] **TASK-004** (done): Define memory read/write protocol and startup context packet. Depends on TASK-003.
- [x] **TASK-005** (done): Define decision log, conflict detection, and approval workflow. Depends on TASK-004.
- [x] **TASK-006** (done): Define task registry, transitions, and handoff format. Depends on TASK-003.
- [x] **TASK-007** (done): Define memory consolidation and concurrent update safeguards. Depends on TASK-004, TASK-005, TASK-006.

## Phase 2 — Agent hierarchy and OpenCode
- [x] **TASK-008** (done): Specify Orchestrator, Manager, Specialist contracts. Depends on TASK-001, TASK-005.
- [x] **TASK-009** (done): Implement OpenCode adapter from verified current conventions. Depends on TASK-002, TASK-008.
- [x] **TASK-010** (done): Add OpenCode startup, task, and handoff workflows. Depends on TASK-004, TASK-006, TASK-009. All four acceptance criteria passed live verification (Crouton Alpha, no paid models); TASK-900 lifecycle documented with persisted transitions. Report: `docs/reviews/2026-11-04-task-010-verification.md`.
- [x] **TASK-011** (done; historical status preserved, acceptance correction in TASK-020): Add adapter conformance and safe regeneration. Depends on TASK-009, TASK-010.
- [x] **TASK-020** (done): Correct TASK-011 adapter regeneration and completion evidence. Depends on TASK-006, TASK-009.

## Phase 3 — Initialization and validation
- [x] **TASK-012** (done): Specify project discovery and interactive initialization. Depends on TASK-001, TASK-002.
- [x] **TASK-013** (done): Implement blueprint generation with collision detection and approval. Depends on TASK-003, TASK-009, TASK-012, TASK-020.
- [ ] **TASK-014**: Implement validation for schemas, task graph, references, and secrets. Depends on TASK-003, TASK-006, TASK-011, TASK-020.
- [ ] **TASK-015**: End-to-end fresh-session continuity test. Depends on TASK-007, TASK-010, TASK-013, TASK-014.

## Phase 4 — Additional providers
- [ ] **TASK-016**: Claude Code adapter. Depends on TASK-011, TASK-015, TASK-020.
- [ ] **TASK-017**: Cursor adapter. Depends on TASK-011, TASK-015, TASK-020.
- [ ] **TASK-018**: Adapter authoring guide and conformance checklist. Depends on TASK-016, TASK-017.

## Observability and monitoring
- [x] **TASK-019** (done): Define provider-neutral observability contract and OpenCode monitor. Depends on TASK-002, TASK-006, TASK-008. Implementation + 23/23 snapshot verification + v2.2.5 visual confirmation complete; `/monitor` hides/shows the sidebar and the monitor reloads after restarting OpenCode. Storage proxy fix committed as `bdfbce1`.

## Scheduling
The Orchestrator selects the next eligible task based on priority, dependencies, and user direction. Do not execute the entire backlog automatically. Surface material decision gates before proceeding.
