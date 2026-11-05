# Architecture Overview

## Architectural layers

1. **Portable Blueprint Core** — provider-independent concepts, directory layout, policies, schemas, templates, lifecycle rules.
2. **Project Memory** — canonical Markdown/JSON records stored in the initialized project and versioned with Git.
3. **Orchestration Model** — USER → ORCHESTRATOR → MANAGERS → SPECIALISTS, including delegation, approvals, conflict handling, and evidence review.
4. **Provider Adapters** — translate core roles, commands, skills, and configuration into each coding agent's native conventions.
5. **Optional Retrieval and Automation** — indexes, embeddings, MCP servers, databases, or automation may accelerate access but are rebuildable and non-authoritative.

## Repository versus initialized project
This repository develops the blueprint. Its root `/memory`, `/tasks`, `/specs`, and `/sessions` track this product's own development.

An initialized target project receives a separate `.blueprint/` directory containing that project's context, state, decisions, tasks, sessions, and handoffs. Provider-specific files are generated or merged outside that canonical store according to adapter rules. The full tree, file catalog, ownership, and collision/upgrade rules are in [Target-Project Blueprint Layout and Ownership](target-project-layout.md).
The discovery interview, confirmation gates, resumable intake, and collision preview are specified in [Project Discovery and Interactive Initialization](project-discovery-and-initialization.md).

## Runtime-neutral operating cycle
`Load Context → Select Task → Plan/Delegate → Execute → Verify → Consolidate Memory → Handoff`.

The cycle is a protocol for agents to follow, not a promise that this repository runs an autonomous orchestration engine.

## Data authority
- Canonical: project-owned Markdown and JSON under `.blueprint/`.
- Provider-native: generated configuration and agent prompts; derived from the core and adapter.
- Derived: search indexes, embeddings, caches; may be deleted and rebuilt.
- Ephemeral: conversation context; useful but never the only copy of important knowledge.

## Baseline constraints
No database or external service is required. File formats, schemas, and adapter behavior must be documented and testable. Provider-specific limitations must be explicit rather than hidden behind a false abstraction.
