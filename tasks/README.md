# Tasks and Backlog

The task registry is the machine-readable status source; task Markdown files under `tasks/items/` contain detailed execution plans. The backlog is a human-readable roadmap. Keep all three synchronized.

## Rules
- Work one task at a time unless the Orchestrator explicitly justifies safe parallelism.
- Verify dependencies before starting.
- Never mark done without evidence.
- Use stable IDs; do not recycle IDs.
- Update `registry.json`, `backlog.md`, current state, and handoff/session records as appropriate.

The authoritative lifecycle, transition matrix, dependency validation, evidence mapping, and handoff requirements are in [Task Lifecycle, Registry, and Handoffs](../docs/architecture/task-lifecycle.md). The registry shape is defined by `schemas/task-registry.schema.json`.
