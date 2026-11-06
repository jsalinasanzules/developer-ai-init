# developer-ai-init-monitor (OpenCode TUI plugin)

Optional sidebar monitor for OpenCode implementing the provider-neutral observability contract (`docs/architecture/observability.md`, v1.0.0). It reads Blueprint canonical state and never writes to it.

Verified against OpenCode `v2.2.5` (2026-11-04). See the spike record `docs/architecture/monitor-spike-2026-11-04.md`.

## What it shows

- Canonical layout detected (`.blueprint/` projects or a root development layout like this repository's).
- Active task (ID, title, status), acceptance-criteria evidence counts, owner role.
- Blockers and pending approvals (or `unparsed` when the narrative can't be read).
- Latest ADR, latest handoff, last canonical state age.
- `configured hierarchy` when the optional machine-readable role file is present; otherwise `configured hierarchy: unavailable` instead of an invented hierarchy.
- `observed runtime` information from OpenCode events: parent/child session links, explicit tool invocations, attempts/outcomes, and a compact five-row activity feed. Runtime data is ephemeral and is never written to canonical records or a second database.
- Explicit `review: unobserved · approval: unobserved` once runtime sessions are observed; neither review nor approval is inferred from a session ending.
- `issues` count when the snapshot degraded (missing/unparsable records) plus runtime observation warnings/unknowns.

Source of truth stays in `.blueprint/` (or the development layout's root equivalents). The monitor mirrors nothing durable.

## Install (target project, optional)

1. Copy `adapters/opencode/monitor` into the generated project at
   `.opencode/plugins/developer-ai-init-monitor/`. No extra configuration file is needed because OpenCode discovers immediate plugin-package directories there.
2. Restart or reload OpenCode (plugins hot-reload on watched config directories).
3. Toggle: `/monitor` or the palette command “Toggle Blueprint monitor sidebar”; the hidden flag persists in TUI storage.

The monitor is optional: it must not be installed by default initializer flows
without user approval, and every workflow works without it (see ADR-008).

## Install (Blueprint development repository)

The same directory can live at `adapters/opencode/monitor` inside this repository. To use it while developing this Blueprint, symlink or copy it under `.opencode/plugins/` here; root resolution then finds the development layout (root `tasks/`, `memory/`, `specs/`, `handoffs/`). No separate implementation exists or should be created (single reusable contract, §2 of the observability contract).

## Files

| Path | Purpose |
| --- | --- |
| `package.json` | name, exports (`.` server part, `./tui` TUI part), peer deps for OpenTUI/solid. |
| `src/index.ts` | Server part: stable plugin id; no behavior; reserved for future event/RPC hooks. |
| `src/blueprint.ts` | Root resolution + snapshot reader (contract §3–§4, §6). READ-ONLY. |
| `src/runtime-observations.ts` | In-memory event/session/tool mapping; pure reducer and no canonical I/O. |
| `src/configured-hierarchy.ts` | Reads optional `.blueprint/config/agents.json`; returns explicit unavailable/degraded state otherwise. |
| `src/tui.tsx` | TUI part: `sidebar.content` slot rendering, `/monitor` toggle, poll refresh, and runtime subscriptions. |

## Refresh and degradation

- Snapshot records parse once per poll (currently once per second) and take effect as an in-memory update; there is no attempt to overlay runtime events onto canonical task state.
- Missing or misshapen events are recorded as `issues`/activity. Duplicate event IDs are ignored. Late terminal/start events do not downgrade a completed or interrupted attempt.
- Disconnected/unavailable runtime listeners are shown as explicitly incomplete. No missing event is treated as completion, review, or approval.
- Missing/unparsable records degrade the snapshot and increment `issues`; the sidebar keeps showing the last good values with a clear issue line instead of hiding the panel.
- If no canonical root resolves, the sidebar shows “not a Blueprint project” and never invents paths.

## Read-only guarantee

`src/blueprint.ts` performs no writes, no network calls, and expands to nothing outside the resolved canonical root. The re-run contract check `scripts/verify-observability-snapshot.ts` proves that reading produces no filesystem changes in the canonical root.
