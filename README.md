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

The repository is at the foundation stage. Detailed architecture documents, specifications, task definitions, memory templates, and the OpenCode adapter will be added incrementally, with decisions validated before implementation.

## Guiding rule

Instructions define how agents operate. Persistent memory records what is known, what has changed, why decisions were made, and what must happen next.
