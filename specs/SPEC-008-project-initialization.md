# SPEC-008 — Project Initialization and Discovery

## Requirements
- INIT-001: The initializer MUST inspect whether the target is an existing or new project.
- INIT-002: It MUST gather project purpose, users, goals, stack, architecture constraints, conventions, and provider preferences through an interactive interview when missing.
- INIT-003: It MUST summarize collected information and request confirmation before generating canonical files.
- INIT-004: It MUST detect existing `.blueprint/` and provider configuration.
- INIT-005: It MUST preview files to create, merge, or skip before writing.
- INIT-006: It MUST never replace user content silently.
- INIT-007: It MUST create initial tasks only after scope and acceptance criteria are clear.
- INIT-008: It MUST support partial answers and mark unknowns explicitly rather than inventing them.
- INIT-009: It MUST distinguish project facts from assumptions and pending questions.

## Acceptance criteria
An initialization flow and generation plan exist for both empty and existing repositories, including collision handling and approval gates.

The design baseline and concrete scenarios are documented in
[`docs/architecture/project-discovery-and-initialization.md`](../docs/architecture/project-discovery-and-initialization.md).
