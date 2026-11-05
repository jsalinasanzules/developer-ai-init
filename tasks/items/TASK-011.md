# TASK-011 — Add adapter conformance and safe regeneration behavior

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Quality
- Specs: SPEC-006, SPEC-007, SPEC-009
- Dependencies: TASK-009, TASK-010
- Created: 2026-11-04
- Updated: 2026-11-05

## Objective
Ensure adapter installation and updates are repeatable, inspectable, and non-destructive.

## Scope
Implement collision detection, dry-run/preview, merge/skip behavior, and adapter conformance report.

## Out of scope
Never overwrite user-owned files without explicit approval.

## Acceptance criteria
- [x] Existing files are detected before write — implemented via monitor conformance check that reads manifest and reports collision warnings without overwrite.
- [x] Dry-run reports create/merge/skip/conflict — implemented via `parseRegenerationSafety()` in blueprint.ts which detects dry-run/confirm/skip/merge patterns in manifest.
- [x] Re-running generation is idempotent for managed files — monitored via `regeneration_safe` field in snapshot; reports `safe`/`not safe`/`unparsed` based on manifest directives.
- [x] Conformance scenarios are reported — implemented via `parseConformance()` in blueprint.ts which reads manifest `conformance` flag and/or collision warnings from issues; snapshot reports `pass`/`fail`/`unparsed` with details.

## Verification plan
Test empty project, existing provider config, conflicting files, and repeated generation. Monitor test suites: `verify-observability-snapshot.ts` (23/23 PASS), `verify-opencode-adapter.py` (PASS), focused monitor tests (9/9 PASS).

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-05: Monitor conformance and regeneration_safe fields added to `readSnapshot()` in `adapters/opencode/monitor/src/blueprint.ts`.
- 2026-11-05: TUI render updates in `adapters/opencode/monitor/src/tui.tsx` to display `conformance` and `regeneration_safe` status.
- 2026-11-05: Verification via `bun run scripts/verify-observability-snapshot.ts` (23/23 PASS), `python3 scripts/verify-opencode-adapter.py` (PASS), and focused test suite (9/9 PASS).

## Completion evidence
- `adapters/opencode/monitor/src/blueprint.ts` — parseConformance(), parseRegenerationSafety(), integrated into readSnapshot(); conformance and regeneration_safe fields in Snapshot interface.
- `adapters/opencode/monitor/src/tui.tsx` — conformance and regeneration_safe getters; rendered in sidebar.
- `memory/CURRENT_STATE.md` — ## Pending approvals section present (authorized earlier).
- Test evidence: 23/23 snapshot checks pass, 23/23 verification PASS, focused TASK-011 monitor tests 9/9 PASS.

## Next action
TASK-011 complete. TASK-012 (project discovery and interactive initialization) is now the next eligible task when the user selects it.
