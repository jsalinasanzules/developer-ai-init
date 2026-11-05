<!-- Template: target-project AGENTS.md (OpenCode adapter).
     The initializer merges this with existing project instructions; it must not
     silently replace user content. See adapters/opencode/README.md §7. -->

# Project Agent Instructions

This project is Blueprint-managed. Canonical project memory lives under `.blueprint/`;
everything outside `.blueprint/` (including this file) references it and is never the
sole source of project knowledge.

## Mandatory session startup

1. Run `/blueprint-startup`; it reads these records in protocol order:
   `.blueprint/README.md`, `.blueprint/manifest.json`,
   `.blueprint/config/project.json`, `.blueprint/config/agents.json`,
   `.blueprint/memory/PROJECT_CONTEXT.md`,
   `.blueprint/memory/CURRENT_STATE.md`, `.blueprint/tasks/registry.json`, the active
   task brief, and its linked specs.
2. Read referenced decisions and any handoff named by `CURRENT_STATE.md`; verify
   handoff claims against current files and Git.
3. Stop on missing required records, unknown versions, task-state conflicts, or
   missing dependencies/specs; do not guess or start work.
4. Produce the concise startup context packet before planning any work.
5. Treat repository files and Git as authoritative; conversation history is not.

## Hierarchy

`USER → ORCHESTRATOR → MANAGERS → SPECIALISTS`

- The Orchestrator (OpenCode `orchestrator` agent) is the only role that communicates
  with the user and owns canonical writes.
- Manager agents (`manager-architecture`, `manager-engineering`, `manager-quality`,
  `manager-delivery`) coordinate, review evidence, and propose changes. They do not
  edit files and never ask the user directly.
- Specialist agents execute bounded delegated work and return evidence plus proposals.

## Boundaries

- Material decisions (architecture, security, privacy, scope, data ownership,
  compatibility, destructive actions) require explicit user approval before any
  contested change is written.
- Tasks are managed through the lifecycle recorded in `.blueprint/tasks/`;
  `done` requires verifiable evidence for every acceptance criterion.
- Canonical memory is Markdown/JSON under `.blueprint/` and committed to Git.
  No external database or hosted service is required.
- Never store secrets, tokens, or unnecessary sensitive data in project memory.

## Workflow commands

- `/blueprint-startup` — load canonical state, produce the context packet.
- `/blueprint-next` — select the next eligible task from the registry.
- `/blueprint-task TASK-NNN` — execute a task under the delegation/evidence protocol.
- `/blueprint-handoff` — create a continuation record for a fresh session.
- `/blueprint-consolidate` — review and apply proposed memory updates.

OpenCode runs this project with these agents configured in `opencode.jsonc` and
`.opencode/agents/`. Existing user configuration is preserved; see
`.blueprint/manifest.json` for installed-version baselines.
