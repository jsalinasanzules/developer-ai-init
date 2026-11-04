# Provider Adapter Architecture

## Purpose
A provider adapter maps the provider-neutral blueprint contract to a coding agent's native configuration and interaction model.

## Adapter responsibilities
- map core roles to provider-native agent/subagent definitions where supported;
- publish the startup and task execution protocol;
- expose commands or skills for initialization, task selection, memory consolidation, and handoff where supported;
- identify provider-specific limitations and required manual steps;
- preserve canonical memory in `.blueprint/`;
- avoid making provider-native configuration the only source of project knowledge.

## Adapter must not
- redefine core task or memory semantics;
- silently remove user-owned configuration;
- claim unsupported delegation or lifecycle behavior;
- require an external database for baseline operation.

## Conformance
Every adapter must pass the same core scenarios: fresh-session context loading, task dependency validation, approval pause on material conflict, evidence-based completion, memory consolidation, safe regeneration, and handoff to a different provider/session.

## Initial provider
OpenCode is the first implementation target. TASK-001 records a dated capability baseline from official documentation; TASK-009 must revalidate the current OpenCode configuration conventions before implementation and must not rely on stale examples or assumed paths.
