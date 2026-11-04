# TASK-002 — Finalize target-project blueprint directory and file ownership

## Metadata
- Status: done
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
- [x] Canonical tree is documented.
- [x] Each file has purpose, owner, write events, and source-of-truth status.
- [x] Root development memory is clearly distinguished from target project memory.
- [x] Collision and upgrade policies are defined.

## Verification plan
Review tree against all specs and confirm no mandatory database/service is introduced.

## Execution log
- 2026-11-04: Re-read SPEC-001 and SPEC-002, the memory model, and the approved ADRs.
- 2026-11-04: Defined the canonical `.blueprint/` tree, file catalog, ownership model, source-of-truth boundaries, and initialization/upgrade collision policy in `docs/architecture/target-project-layout.md`.
- 2026-11-04: Aligned the summary tree in `docs/architecture/memory-model.md` and linked the authoritative layout from the README and architecture overview.
- 2026-11-04: Confirmed the design requires only local files and Git; derived data is optional and rebuildable.

## Completion evidence
- Canonical tree: §3 of [target-project-layout.md](../../docs/architecture/target-project-layout.md).
- Per-file purpose, owner, write events, and source-of-truth status: §4.
- Root-versus-target separation: §6.
- Collision and upgrade policies: §7 and §8.
- No mandatory database or network service: §2, §8, and §9.
- Link and JSON checks run after the documentation changes (see repository verification log).

## Next action
None. TASK-002 is done; TASK-003 is eligible once this result is committed.
