# Current Architecture Memory

Provider-agnostic blueprint core + project-owned persistent memory + hierarchical orchestration protocol + provider adapters + optional retrieval/automation.

## Authority
USER → ORCHESTRATOR → MANAGERS → SPECIALISTS. Only Orchestrator communicates with the user. Managers coordinate domains; specialists execute bounded tasks and report evidence/proposals.

## Memory authority
Canonical target-project records live under `.blueprint/`. Provider-native files map roles/workflows to native tooling. Derived indexes/caches are rebuildable. Conversation history is ephemeral.

## Scope separation
This repository's development memory lives at root `/memory`. An initialized target project receives its own `.blueprint/memory/`. Never merge these scopes.

## Provider adapter baseline
OpenCode is the first adapter. ADR-006 selects V2-native generation as the baseline, with portable Markdown commands/skills where practical and V1 limitations documented. ADR-007 permits opt-in depth-2 delegation (`experimental.subagent_depth: 2`) with a sequential fallback because OpenCode defaults to depth 1.

## Pending details
Target directory tree, config schemas, adapter manifest, initializer implementation language/package, and safe upgrade strategy are to be finalized in tasks. TASK-002 owns the target-project layout.
