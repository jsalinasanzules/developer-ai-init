# TASK-021 live evidence — OpenCode 2.2.5

Status: partial. The monitor loads and the user confirmed `/monitor` hide/show in OpenCode v2.2.5. The interactive sidebar was not captured here with runtime/delegation rows; no live PASS is claimed.

## Reproducible checks already observed

1. `opencode --version` → `opencode v2.2.5`.
2. `opencode --standalone --log-level debug --print-logs` in this repository → plugin load events include:
   - `stage=read` with target `src/tui.tsx`
   - `stage=setup` with `plugin=developer-ai-init-monitor`
   - no monitor load error.
3. The user confirmed interactively:
   - `Blueprint Monitor` is visible;
   - `/monitor` hides and shows it;
   - no startup/load errors;
   - live event/delegation rows were not confirmed.

## Delegation runbook

This is a reproducible manual check, not evidence until the user confirms it in the running TUI.

1. Open this repository with `opencode --standalone --log-level debug --print-logs`.
2. Confirm `Blueprint Monitor` is visible and `/monitor` toggles it.
3. Ask the Orchestrator to delegate to `MANAGER: Quality` or an Explore subagent with a deterministic work item such as:
   - `Review one function in adapters/opencode/monitor/src/runtime-observations.ts`
   - return one sentence and cite one exact line/path.
4. Wait for child result.
5. Look for one or more of:
   - `observed runtime: 1 session` or more;
   - a visible delegation row with agent/work-item name and certainty `explicit`, `candidate`, `ambiguous`, or `unresolved`;
   - `parent unobserved` if the parent is not observed;
   - `review: unobserved`, `approval: unobserved`;
   - a recent runtime activity line tied to the delegation.
6. Capture the sidebar text or screenshot and save it beside this README. Do not mark AC-07/AC-09 PASS unless the runtime/delegation rows are actually visible.

## Deterministic checks

- `bun test tests/monitor-runtime-observations.test.ts` → previously reported 20 pass, 43 expect() calls.
- `bun run scripts/verify-observability-snapshot.ts` → previously reported RESULT: PASS.

## Unobserved / missing

- No live capture was produced in this environment.
- No claim is made that rows appeared from the previous load-only check.
