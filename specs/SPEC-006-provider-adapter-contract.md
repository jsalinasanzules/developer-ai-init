# SPEC-006 — Provider Adapter Contract

## Requirements
- ADAPT-001: Adapters MUST implement the provider-neutral role and memory contracts.
- ADAPT-002: Adapters MUST document native capabilities, limitations, and manual setup.
- ADAPT-003: Adapters MUST preserve `.blueprint/` as canonical memory.
- ADAPT-004: Adapters MUST support startup context loading and task/handoff workflows, directly or through documented manual prompts.
- ADAPT-005: Adapters MUST detect existing configuration and avoid destructive overwrite.
- ADAPT-006: Adapters MUST expose a conformance report.
- ADAPT-007: Adapter-specific generated files MUST be reproducible from documented inputs where feasible.

## Adapter manifest (proposed)
Provider ID, adapter version, supported blueprint versions, native role mapping, generated paths, required capabilities, optional capabilities, limitations, and conformance status.

## Acceptance criteria
A provider-neutral adapter contract and a checklist usable by a second provider are documented.
