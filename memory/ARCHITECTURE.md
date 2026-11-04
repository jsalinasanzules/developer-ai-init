# Current Architecture Memory

Provider-agnostic blueprint core + project-owned persistent memory + hierarchical orchestration protocol + provider adapters + optional retrieval/automation.

## Authority
USER → ORCHESTRATOR → MANAGERS → SPECIALISTS. Only Orchestrator communicates with the user. Managers coordinate domains; specialists execute bounded tasks and report evidence/proposals.

## Memory authority
Canonical target-project records live under `.blueprint/`. Provider-native files map roles/workflows to native tooling. Derived indexes/caches are rebuildable. Conversation history is ephemeral.

## Scope separation
This repository's development memory lives at root `/memory`. An initialized target project receives its own `.blueprint/memory/`. Never merge these scopes.

## Pending details
Target directory tree, config schemas, adapter manifest, initializer implementation language/package, and safe upgrade strategy are to be finalized in tasks.
