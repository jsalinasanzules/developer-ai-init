# Manager Quality Review — TASK-021

Task: TASK-021
Reviewer role: MANAGER: Quality
Independent review: YES
Decision: REJECTED
Date: 2026-11-06

## Review scope and method

Independent review of TASK-021 as an `in_review` task. The reviewer did not modify the implementation or tests. Sources reviewed:

- `tasks/items/TASK-021.md`
- `docs/architecture/monitor-live-tracking-discovery-2026-11-06.md`
- `adapters/opencode/monitor/src/runtime-observations.ts`
- `adapters/opencode/monitor/src/configured-hierarchy.ts`
- `adapters/opencode/monitor/src/tui.tsx`
- `adapters/opencode/monitor/README.md`
- `tests/monitor-runtime-observations.test.ts`
- `scripts/verify-observability-snapshot.ts`
- SPEC-006 `ADAPT-001`–`ADAPT-007` and SPEC-007 `OC-001`–`OC-008`

The review evaluates the evidence as documented. It does not invent live-event confirmation and does not treat the task as complete.

## Verification evidence checked

- `bun test tests/monitor-runtime-observations.test.ts` → 20 pass, 43 expect() calls.
- `bun run scripts/verify-observability-snapshot.ts` → published checks PASS.
- One authorized local Crouton Alpha v2.2.5 delegation check returned `blueprint fixture`; it did not prove interactive TUI rendering or live sidebar event rows.
- The user interactively confirmed in OpenCode v2.2.5 that `Blueprint Monitor` is visible, `/monitor` hides and shows it, and no startup/load errors appeared. The user did not confirm runtime/delegation rows.

## AC evaluation

| Criterion | Assessment | Evidence and rationale |
|---|---|---|
| AC-01 | PASS | `docs/architecture/monitor-live-tracking-discovery-2026-11-06.md` documents v2.2.5 event/hooks, payload fields, correlation limits, sources, and unsupported assumptions. Deterministic event tests exercise representative event shapes. |
| AC-02 | PARTIAL | `configured-hierarchy.ts` reads `.blueprint/config/agents.json` or reports `unavailable`; `tui.tsx` keeps configured hierarchy and observed runtime separate. However, no automated test proves rendering of a valid configured hierarchy or prevents configured roles from being mistaken for active sessions. |
| AC-03 | PARTIAL | The reducer and TUI avoid inventing task association or delegation edges: child links require `parentID`, delegation links require matching invocation evidence, and unobserved parents remain labelled. However, the live sidebar display of delegation details was not verified, and there is no integrated canonical-plus-runtime UI test. |
| AC-04 | PARTIAL | The data model separates assignment/delegation, execution attempts, terminal outcomes, and idle; tests cover late create/idle not overwriting terminal state and interruption/failure not implying approval. There is no UI/render test confirming these distinctions to the user. |
| AC-05 | PARTIAL | Duplicate IDs are ignored, out-of-order terminal events do not downgrade terminal attempts, and unsupported events remain activity without invented relations. The feed code caps activity at 100 and renders the last five entries, but ordering/cap behavior lacks dedicated tests and the live feed was not observed. |
| AC-06 | PASS | Parallel, malformed, missing-ID, unparseable-input, failed, interrupted, and disconnected cases are covered by deterministic tests without synthesized completion. |
| AC-07 | BLOCKED | The monitor remains in the existing OpenCode sidebar and preserves toggle behavior. The user confirmed title, `/monitor`, and no load errors, but did not confirm hierarchy/task-delegation details or runtime activity rows in a live sidebar. AC-07 requires those elements to be presented; that live presentation remains unverified. This is not a PASS. |
| AC-08 | PASS | The new runtime layer is in-memory and read-only; the snapshot verifier reports no canonical writes. No database, hosted service, network dependency, or second persistent store was introduced by the TASK-021 implementation. |
| AC-09 | BLOCKED | Deterministic tests and snapshot verification pass. One delegation ran, and load/toggle behavior was confirmed. Live event/delegation behavior was not observed. AC-09 allows a documented limitation only without claiming a pass; it cannot be treated as fully verified live behavior. |

## Accepted limitations

The following limitations are correctly documented and must not be overstated:

- Live event subscription and delegation rows in the TUI were not verified.
- The Crouton Alpha delegation check does not prove the live sidebar event path.
- Review and approval remain `unobserved` when canonical records do not state them; they are not inferred from session completion.
- Event loss/disconnect remains possible by contract and must remain visibly incomplete.
- The unrelated bundled presentation heuristics in `adapters/opencode/monitor/src/blueprint.ts` are excluded from TASK-021 evidence.
- No observability-contract change was made.

These limitations are honest, but they do not satisfy the full AC-07 and AC-09 requirements for completion. They therefore remain blockers for `done`, not evidence to convert AC-07 or AC-09 into live PASS results.

## Blocking findings

1. **AC-07 live UI/RUNTIME delegation rows unverified.** The user confirmed only plugin load, visible title, `/monitor`, and absence of load errors. The UI must still be shown presenting hierarchy, task/delegation details, and recent activity.
2. **AC-09 live event behavior unverified.** Delegation execution completed, but the event-driven sidebar path was not rendered/inspected. No live behavior PASS may be claimed.
3. **Configured hierarchy has no behavioral test.** The implementation reads `.blueprint/config/agents.json`, but there is no automated test proving that valid roles are shown and malformed/missing entries degrade honestly.
4. **No UI/render regression test.** The runtime reducer is well tested, but no test renders the sidebar data path or confirms critical labels and bounded feed.
5. **Completion-evidence formal gap.** The brief’s acceptance checkboxes are not marked and its evidence rows lack the exact criterion text and concrete named-test references required by the completion gate.
6. **No gate-ready verification record.** The brief lacks a `Verification results` section with exact commands and a linked report, and no Manager review was previously recorded in the brief for the gate.

## Non-blocking findings

- The feed ordering is stable and the live rows were not observed, so the current oldest-to-newest display is a minor UX choice rather than a correctness defect.
- The snapshot verifier relaxes the task count to `>= 20`; acceptable after TASK-021 was added.
- The stray `.opencode/` alias was previously authorized for removal and is outside TASK-021 evidence.

## Recommendation

Task stay `in_review`. The next step is not to force `done`: add the missing configured-hierarchy and UI/reducer regression tests, complete the live v2.2.5 sidebar verification, record the exact evidence mapping for every AC, and resubmit for a new Manager review. Do not mark AC-07 or AC-09 as PASS live until the corresponding behavior is actually observed.
