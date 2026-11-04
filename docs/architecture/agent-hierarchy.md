# Agent Hierarchy and Responsibilities

```text
USER
  └── ORCHESTRATOR (only user-facing agent)
        ├── MANAGER: Architecture
        │     └── SPECIALISTS: domain design, integration analysis
        ├── MANAGER: Engineering
        │     └── SPECIALISTS: backend, frontend, platform
        ├── MANAGER: Quality
        │     └── SPECIALISTS: testing, security review
        └── MANAGER: Delivery
              └── SPECIALISTS: documentation, release preparation
```

## USER
Owns product intent, priorities, and approval of material decisions. The user may initiate or change goals at any time.

## ORCHESTRATOR
The user's sole counterpart. Loads memory, classifies requests, detects conflicts, plans work, selects managers, validates outputs, asks for approvals, and consolidates shared memory. It must not delegate away accountability.

## MANAGERS
Coordinate a domain, decompose approved scope, assign bounded work, review specialist evidence, resolve ordinary domain-level implementation details within approved constraints, and report to the Orchestrator.

## SPECIALISTS
Execute bounded tasks, inspect relevant files/specs, return changed-file lists, verification evidence, risks, and proposed memory updates. They do not independently redefine scope or overwrite shared memory.

## Role activation
Roles are logical responsibilities. An adapter may map them to native subagents, agents, modes, skills, or sequential prompts. The core does not require concurrent agents or a particular provider feature.

## Delegation contract
Every delegation includes objective, context references, allowed scope, forbidden changes, dependencies, expected artifacts, acceptance criteria, and reporting format.

## Escalation path
Specialists report conflicts to their manager; managers forward material conflicts to the Orchestrator; only the Orchestrator asks the user. Conflict classification, the approval packet, attribution, expiry, and decision supersession are defined in [Decision, Conflict, and Approval Protocol](decision-and-approval-protocol.md).
