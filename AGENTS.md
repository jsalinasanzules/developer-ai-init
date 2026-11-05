# Repository Agent Instructions

## Mission
Build Developer AI Init as a provider-agnostic, Git-native blueprint for project initialization, hierarchical coding-agent orchestration, and portable persistent memory.

This repository is the blueprint's source project. Do not confuse its own development memory at `/memory` with the target-project memory generated under `.blueprint/memory/`.

## Mandatory session startup
1. Read this file and `README.md`.
2. Read `memory/PROJECT_CONTEXT.md` and `memory/CURRENT_STATE.md`.
3. Read `tasks/registry.json` and `tasks/backlog.md`.
4. Identify one eligible task; read its specification, dependencies, and relevant decisions.
5. Inspect the actual repository state before editing. Treat Git as the source of truth.
6. Produce the startup context packet defined in `docs/architecture/memory-protocol.md` before planning work.

## Hierarchy
`USER → ORCHESTRATOR → MANAGERS → SPECIALISTS`.

- The Orchestrator is the only agent that communicates decisions and questions to the user.
- Managers coordinate bounded domains and review specialist output.
- Specialists execute narrowly scoped work and return evidence plus proposed memory updates.
- Roles describe responsibilities; they do not require every role to run as a separate process.
- Do not allow specialists to make unapproved material decisions or directly overwrite shared canonical memory.

## Decision and conflict protocol
Stop and ask the user through the Orchestrator when:
- instructions conflict or a requirement is materially ambiguous;
- a change affects architecture, security, privacy, data ownership, compatibility, scope, or infrastructure;
- an operation is destructive, irreversible, costly, or changes user-owned data;
- a task's acceptance criteria cannot be met without changing its scope.

Do not silently choose a side, invent missing requirements, or treat a model's preference as user approval. Record approved material decisions in `memory/DECISIONS.md`.

## Task execution
- Work on one task at a time by default.
- Check dependencies and task status before starting.
- Follow the linked specification and acceptance criteria.
- Keep changes within task scope.
- Verify with relevant checks; report exact commands and outcomes.
- A task is `done` only when acceptance criteria have evidence.
- In this source repository, transition `in_review` to `done` only through
  `python3 scripts/task_lifecycle.py complete TASK-NNN --review <review-artifact> --next-action "<next action>" --apply`.
  This Python gate is internal tooling and must not be copied into generated
  projects or create a Python runtime requirement there.
- If blocked, record the blocker and next action; do not disguise partial work as completion.

## Persistent memory
Canonical project memory is Markdown/JSON under `.blueprint/` in projects initialized by this blueprint. Markdown/JSON are authoritative and Git-versioned. Provider context, vector indexes, databases, and MCP tools are optional accelerators, never the only source of truth.

For this repository, use the top-level `/memory` directory as its development memory. Update the owning record after meaningful discoveries, approved decisions, task transitions, or handoffs. Follow the read order, ownership map, write triggers, non-write cases, and compaction rules in `docs/architecture/memory-protocol.md`. Do not store credentials, tokens, secrets, or unnecessary sensitive personal data.

## Safe editing
- Inspect before modifying; preserve user changes.
- Never overwrite an existing file without reading it and understanding its purpose.
- Do not add dependencies, databases, infrastructure, or provider-specific assumptions without a task/spec and approval where material.
- Prefer small, reviewable commits with descriptive messages.
- Do not claim a command, test, or external action succeeded unless it was actually run and observed.

## End-of-task requirements
Update task records and relevant memory, then report:
1. scope completed;
2. files changed;
3. verification evidence;
4. decisions/questions for the user;
5. memory updated;
6. next eligible task and dependencies.
Create a handoff when another session or LLM should continue.
