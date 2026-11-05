import { Plugin } from "@opencode/plugin"

/**
 * Server part of the Blueprint monitor. The TUI part does all presentation;
 * the server part exists so the plugin id is stable and so future integrations
 * (events, RPC) have a home. It must never write canonical Blueprint records.
 */
export default Plugin.define({
  id: "developer-ai-init-monitor",
  async setup(_ctx) {
    // Intentionally empty: reading is performed in the TUI part. Server-side
    // event hooks are reserved for future contract versions.
  },
})
