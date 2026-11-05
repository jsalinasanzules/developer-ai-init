# developer-ai-init-monitor (OpenCode TUI plugin)

Optional sidebar monitor for OpenCode implementing the provider-neutral observability contract (`docs/architecture/observability.md`, v1.0.0). It reads Blueprint canonical state and never writes to it.

Verified against OpenCode `v2.2.5` (2026-11-04). See the spike record `docs/architecture/monitor-spike-2026-11-04.md`.

## What it shows

- Canonical layout detected (`.blueprint/` projects or a root development layout like this repository's).
- Active task (ID, title, status), acceptance-criteria evidence counts, owner role.
- Blockers and pending approvals (or `unparsed` when the narrative can't be read).
- Latest ADR, latest handoff, last canonical state age.
- `issues` count when the snapshot degraded (missing/unparsable records).

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
| `src/tui.tsx` | TUI part: `sidebar.content` slot rendering, `/monitor` toggle, poll refresh. |

## Refresh and degradation

- By default the TUI re-reads canonical mtimes at most 1×/s and re-reads only changed files. The staleness shown is advisory (`stale: true` past a configurable threshold).
- Missing/unparsable records degrade the snapshot and increment `issues`; the sidebar keeps showing the last good values with a clear issue line instead of hiding the panel.
- If no canonical root resolves, the sidebar shows “not a Blueprint project” and never invents paths.

## Read-only guarantee

`src/blueprint.ts` performs no writes, no network calls, and expands to nothing outside the resolved canonical root. The re-run contract check `scripts/verify-observability-snapshot.ts` proves that reading produces no filesystem changes in the canonical root.
