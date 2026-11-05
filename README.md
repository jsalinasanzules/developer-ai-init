# Developer AI Init

A provider-agnostic blueprint for initializing software projects with hierarchical AI coding agents and portable persistent project memory.

## Purpose

Developer AI Init provides a reusable project structure, operating protocols, specifications, and provider adapters. It is a blueprint and initialization framework, not an autonomous agent runtime or hosted agent-management platform.

## Core principles

- **Portable memory:** project-owned Markdown and JSON files are the canonical source of truth.
- **Provider independence:** project continuity must not depend on a single model, vendor, or conversation history.
- **Hierarchical orchestration:** USER → ORCHESTRATOR → MANAGERS → SPECIALISTS. The Orchestrator is the only user-facing agent.
- **Explicit decisions:** material conflicts, architectural changes, security implications, and destructive actions require user approval.
- **Evidence-based progress:** tasks are completed only when their acceptance criteria have been verified.
- **Git-native by default:** canonical memory and project artifacts are version-controlled; databases and external retrieval services are optional.

## Planned capabilities

1. Portable Blueprint Core
2. Persistent Project Memory
3. Hierarchical Agent Roles
4. Orchestration and Conflict Resolution
5. Task Lifecycle and Handoffs
6. Provider Adapter Contract
7. OpenCode Adapter (first integration)
8. Project Initialization and Discovery
9. Validation and Conformance

## Repository status

The foundation baseline is in place: architecture documents, specifications, task briefs, memory records, and lifecycle protocols. The OpenCode adapter and versioned schemas are implemented. TASK-013 adds a source-only, approval-gated generator for the canonical `.blueprint/` tree and selected adapter files; interactive discovery remains an Orchestrator workflow, and schema/task-graph validation is tracked separately in TASK-014.

## Guiding rule

Instructions define how agents operate. Persistent memory records what is known, what has changed, why decisions were made, and what must happen next.

## Repository navigation

- [Vision](docs/vision.md)
- [Architecture overview](docs/architecture/overview.md)
- [Target-project layout and ownership](docs/architecture/target-project-layout.md)
- [Project discovery and interactive initialization](docs/architecture/project-discovery-and-initialization.md)
- [Blueprint generation and approval](docs/architecture/blueprint-generation.md)
- [Persistent memory model](docs/architecture/memory-model.md)
- [Memory read/write protocol](docs/architecture/memory-protocol.md)
- [Decision, conflict, and approval protocol](docs/architecture/decision-and-approval-protocol.md)
- [Agent hierarchy](docs/architecture/agent-hierarchy.md)
- [Task lifecycle](docs/architecture/task-lifecycle.md)
- [Provider adapters](docs/architecture/provider-adapters.md)
- [Specifications index](specs/README.md)
- [JSON schemas and fixtures](schemas/README.md)
- [TASK-001 foundation review](docs/reviews/2026-11-04-task-001-foundation-review.md)
- [Task backlog](tasks/backlog.md)
- [Task registry](tasks/registry.json)
- [Development memory](memory/README.md)
- [Agent operating instructions](AGENTS.md)

## How to continue

Start every new LLM session with the repository instructions in `AGENTS.md`. Read `memory/PROJECT_CONTEXT.md`, `memory/CURRENT_STATE.md`, and `tasks/registry.json`; then open the active task and its linked specifications. Execute one task at a time, verify its acceptance criteria, and update task status and persistent memory before handing off.
