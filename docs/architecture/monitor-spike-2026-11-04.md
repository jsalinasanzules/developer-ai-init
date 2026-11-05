# Monitor Compatibility Spike — OpenCode 2.2.5 (TASK-019)

- Date: 2026-11-04
- Environment: OpenCode `v2.2.5`, macOS (darwin), TUI plugin installed at `.opencode/plugins/developer-ai-init-monitor/` inside a simulated target project with a minimal canonical `.blueprint/` (registry with 2 tasks, `CURRENT_STATE.md` with an active ready task, one ADR, one handoff, project.json, manifest.json).

## Methods

Because the TUI is interactive, the spike was executed with a pseudo-tty capture
(`script -q`) and observed outputs; the TUI itself cannot be asserted from logs
alone, so plugin-load errors were captured by rerunning with
`--standalone --log-level debug --print-logs`.

## Verified on 2.2.5

1. **TUI starts against the spike project** — banner and prompt render normally
   (`OpenCode` ASCII banner, `Build · GLM-5.3-Flash Free`, 2.2.5 version badge),
   exit code 0.
2. **Plugin fully loads and initializes on 2.2.5** (captured with
   `--standalone --log-level debug --print-logs`):
   - server part: `msg="loading plugin" id=…/.opencode/plugins/developer-ai-init-monitor entrypoint=…/src/index.ts` and a file watcher subscription;
   - TUI part: `message="plugin operation started" … stage=read` for `src/tui.tsx`, then `message="plugin operation completed" … stage=setup plugin=developer-ai-init-monitor`;
   - no error/failure lines mentioning the monitor plugin or `tui.tsx`.
3. **Slot API availability** — `sidebar.content` slot keys exist in 2.2.5 per
   official OpenCode v2.2.x TUI plugin documentation (`/v2/docs/build/plugins/cli`).
4. **Contract reader standalone verification** — `bun run scripts/verify-observability-snapshot.ts`
   → `RESULT: PASS` (23/23 checks: root resolution for both layouts, registry
   mirror, active-task selection, evidence counts, blockers/approvals parsing,
   decisions, handoffs, no-write proof).

## Findings and constraints

- The sidebar renders only when the TUI has room and a focusable session/home
  state; in an 80×24 pty capture the sidebar may not be drawn even when the
  plugin loads. Compatibility claims therefore rely on (a) plugin load success
  in the 2.2.5 runtime and (b) the official slot contract for `sidebar.content`.
- Plugins are loaded per platform from local directories; the monitor requires
  no additional configuration beyond being placed under `.opencode/plugins/`.
- The monitor's contract reader runs without an OpenCode process, so the shared
  root logic can be regression-checked in CI (contract §9).

## Observed run excerpt (2.2.5)

- `opencode` TUI session seeded with the spike project; TUI exit code 0.
- Debug run: server started with the spike project's configuration; log captured
  to `/tmp/oc-logfile.log` for plugin-load events (see §Verified 2 for where the
  important lines live).

## Honest limitations

- The interactive TUI was not asserted to draw the panel on 2.2.5 from a purely
  automated session (no stable headless TUI hook). What IS verified: the plugin
  loads in the 2.2.5 runtime without breaking the TUI, and the TUI remains
  fully usable. Whether the sidebar still renders with future releases must be
  re-verified when OpenCode updates (the monitor remains compatible via the
  public slot contract and deps pinning).
- The monitor never rendered "not a Blueprint project" in the spike because the
  root resolution logically cannot be shown absent a canonical root; that path
  is proven in the snapshot tests (Context D) instead.
