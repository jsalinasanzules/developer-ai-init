# SPEC-001 — Portable Blueprint Core

## Purpose
Define the provider-neutral structure and baseline behavior that can be installed into software projects.

## Scope
Directory layout, configuration boundaries, templates, versioning, ownership, and safe initialization/update behavior. Excludes a hosted runtime.

## Requirements
- CORE-001: The blueprint MUST separate provider-neutral core artifacts from provider-specific adapter files.
- CORE-002: The initialized project MUST contain a `.blueprint/` canonical directory.
- CORE-003: The baseline MUST work using local Markdown/JSON files and Git only.
- CORE-004: Provider configuration MUST reference core roles and MUST NOT be the sole source of truth.
- CORE-005: Initialization MUST detect path collisions before writing.
- CORE-006: Existing user-owned files MUST NOT be overwritten without explicit approval.
- CORE-007: The blueprint MUST identify its schema/version and support documented upgrades.
- CORE-008: Optional integrations MUST be clearly marked optional.

## Acceptance criteria
1. A documented target-project tree exists.
2. File ownership and canonical-versus-derived data are explicit.
3. Collision and regeneration behavior is specified.
4. Baseline operation does not require a database or network service.

## Dependencies
None. Related: SPEC-002, SPEC-006, SPEC-008.
