# Project Context

Developer AI Init is a provider-agnostic blueprint and initializer for software projects using hierarchical AI coding agents and portable persistent memory.

## Problem
Project context, architecture decisions, task progress, and constraints can be lost when coding-agent sessions end or when switching LLM/provider.

## Intended outcome
A project carries its own operating instructions, roles, specifications, task state, memory, and handoffs in Git-versioned files so a fresh session or different LLM can continue reliably.

## Non-goals
- Hosted SaaS or autonomous agent runtime.
- Mandatory PostgreSQL, Supabase, vector database, or remote memory service.
- OpenCode-specific configuration as canonical project memory.
- Independent authority for subagents to change product direction or material architecture.

## Agreed direction
- Canonical memory: project-owned Markdown/JSON versioned with Git.
- Optional hybrid retrieval: indexes, vector stores, MCP, and databases may be derived accelerators, never baseline requirements.
- Hierarchy: USER → ORCHESTRATOR → MANAGERS → SPECIALISTS.
- Orchestrator is the only user-facing agent.
- OpenCode is first adapter; Claude Code and Cursor are later candidates.
- This is a reusable blueprint, not a full agent orchestration system.

## Open questions
Implementation language, packaging/distribution, initializer UX, schema validation tooling, and exact provider mappings remain undecided. Do not invent decisions.
