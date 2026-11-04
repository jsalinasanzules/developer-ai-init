# Product Vision

## Problem
AI coding sessions are often ephemeral. Project-critical context, decisions, task status, and implementation constraints can remain trapped in a provider's conversation history or agent-specific configuration. Switching models, tools, or sessions can therefore cause context loss, duplicated work, and inconsistent decisions.

## Vision
Developer AI Init is a portable blueprint that gives software projects a durable operating structure for AI-assisted development: explicit project context, hierarchical roles, task specifications, decision records, persistent memory, handoffs, and provider adapters.

## What it is
- A reusable repository blueprint and project initializer.
- A set of documented protocols, schemas, templates, and validation rules.
- A provider-agnostic core with OpenCode as the first adapter.
- A Git-native memory model whose canonical data is human-readable Markdown and structured JSON.

## What it is not
- Not an autonomous agent runtime.
- Not a hosted SaaS platform or central agent manager.
- Not dependent on PostgreSQL, Supabase, vector databases, or a remote memory service.
- Not a replacement for the coding agent's native capabilities.
- Not permission for agents to make product or architectural decisions without the user.

## Design principles
1. **Portability:** canonical project knowledge belongs to the project.
2. **Provider neutrality:** adapters translate the core contract into native provider conventions.
3. **Human authority:** the user retains authority over goals and material decisions.
4. **Single point of communication:** only the Orchestrator communicates with the user.
5. **Traceability:** decisions, tasks, evidence, and handoffs are inspectable and versioned.
6. **Minimal required infrastructure:** local files and Git are sufficient for the baseline.
7. **Progressive enhancement:** search indexes, MCP tools, databases, and automation may be added optionally.
8. **Safe regeneration:** initialization and updates preserve user-owned content and detect collisions.

## Initial delivery strategy
Establish the core model and contracts first, then define memory/task schemas, then implement the OpenCode adapter, then build project discovery and initialization, then validate cross-session continuity. Additional providers follow only after the adapter contract is stable.
