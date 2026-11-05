# TASK-020 independent Manager review — changes requested

Date: 2026-11-05

Task: TASK-020  
Reviewer role: MANAGER: Quality  
Independent review: YES  
Decision: CHANGES REQUESTED

## Findings

1. **AC-01 and AC-03 — directory collision can partially write.** An exact-path
   overwrite approval on a directory target leaves no planned content, but
   marks the conflict approved. The apply phase can write earlier planned
   outputs before reaching that target and failing. Reject approvals for
   non-regular targets during plan validation so all conflicts are detected
   before any writes. See `scripts/regenerate_opencode_adapter.py`.
2. **AC-06 — missing named-test evidence is not directly tested.** The negative
   suite checks a missing evidence row, but not a row naming a nonexistent test
   function. Add a negative case proving such evidence blocks completion with
   no canonical writes. See `tests/test_task_lifecycle.py`.
3. **Snapshot regression — resolved as an expectation mismatch.** After
   TASK-020 moved to `in_review`, `bun run
   scripts/verify-observability-snapshot.ts` returned `RESULT: FAIL`: its
   development-layout assertions still required an active task and active-task
   evidence. The documented selection protocol only selects `in_progress`, or
   an eligible `ready` task; it does not select `in_review`. Preserve that
   contract and update the snapshot assertions to check that TASK-020 remains
   visible in the registry as `in_review`, while no active task is fabricated.

## Criterion summary

- AC-01, AC-03: blocked by finding 1.
- AC-02, AC-04, AC-07: supported by code and test evidence.
- AC-05: implementation and positive/negative coverage are present; rerun the
  completion gate after the snapshot expectation is corrected.
- AC-06: blocked until the missing named-test negative case is added.

## Resolution record

The snapshot test now follows the memory-protocol active-task selection
contract; no monitor behavior or lifecycle selection rules were changed.
