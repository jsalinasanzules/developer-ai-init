# Development Memory

This folder stores durable context for development of this blueprint repository. It is separate from the `.blueprint/memory/` folder created inside initialized projects.

At every session start, read `PROJECT_CONTEXT.md`, `CURRENT_STATE.md`, `../tasks/registry.json`, the active task and its specifications, then relevant decisions and conventions.

Update the owning record when facts change. Keep current state concise, preserve decision history, synchronize task status, and never store credentials or secrets.
