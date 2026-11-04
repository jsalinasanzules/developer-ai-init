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
- [ ] **TASK-007** (ready): Define memory consolidation and concurrent update safeguards. Depends on TASK-004, TASK-005, TASK-006.

## Phase 2 — Agent hierarchy and OpenCode
- [ ] **TASK-008** (ready): Specify Orchestrator, Manager, Specialist contracts. Depends on TASK-001, TASK-005.
- [ ] **TASK-009**: Implement OpenCode adapter from verified current conventions. Depends on TASK-002, TASK-008.
- [ ] **TASK-010**: Add OpenCode startup, task, and handoff workflows. Depends on TASK-004, TASK-006, TASK-009.
- [ ] **TASK-011**: Add adapter conformance and safe regeneration. Depends on TASK-009, TASK-010.

## Phase 3 — Initialization and validation
- [ ] **TASK-012**: Specify project discovery and interactive initialization. Depends on TASK-001, TASK-002.
- [ ] **TASK-013**: Implement blueprint generation with collision detection and approval. Depends on TASK-003, TASK-009, TASK-012.
- [ ] **TASK-014**: Implement validation for schemas, task graph, references, and secrets. Depends on TASK-003, TASK-006, TASK-011.
- [ ] **TASK-015**: End-to-end fresh-session continuity test. Depends on TASK-007, TASK-010, TASK-013, TASK-014.

## Phase 4 — Additional providers
- [ ] **TASK-016**: Claude Code adapter. Depends on TASK-011, TASK-015.
- [ ] **TASK-017**: Cursor adapter. Depends on TASK-011, TASK-015.
- [ ] **TASK-018**: Adapter authoring guide and conformance checklist. Depends on TASK-016, TASK-017.

## Scheduling
The Orchestrator selects the next eligible task based on priority, dependencies, and user direction. Do not execute the entire backlog automatically. Surface material decision gates before proceeding.
