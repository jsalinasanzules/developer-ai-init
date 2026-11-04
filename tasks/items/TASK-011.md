# TASK-011 — Add adapter conformance and safe regeneration behavior

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Quality
- Specs: SPEC-006, SPEC-007, SPEC-009
- Dependencies: TASK-009, TASK-010
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Ensure adapter installation and updates are repeatable, inspectable, and non-destructive.

## Scope
Implement collision detection, dry-run/preview, merge/skip behavior, and adapter conformance report.

## Out of scope
Never overwrite user-owned files without explicit approval.

## Acceptance criteria
- [ ] Existing files are detected before write.
- [ ] Dry-run reports create/merge/skip/conflict.
- [ ] Re-running generation is idempotent for managed files.
- [ ] Conformance scenarios are reported.

## Verification plan
Test empty project, existing provider config, conflicting files, and repeated generation.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
