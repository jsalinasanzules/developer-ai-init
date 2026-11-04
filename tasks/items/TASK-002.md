# TASK-002 — Finalize target-project blueprint directory and file ownership

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-001, SPEC-002
- Dependencies: TASK-001
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Define the canonical .blueprint directory installed in target projects and specify ownership and update rules for every file.

## Scope
Produce target tree, file catalog, canonical/derived/provider-native classification, and safe upgrade rules.

## Out of scope
Do not implement initializer or provider-specific config.

## Acceptance criteria
- [ ] Canonical tree is documented.
- [ ] Each file has purpose, owner, write events, and source-of-truth status.
- [ ] Root development memory is clearly distinguished from target project memory.
- [ ] Collision and upgrade policies are defined.

## Verification plan
Review tree against all specs and confirm no mandatory database/service is introduced.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
