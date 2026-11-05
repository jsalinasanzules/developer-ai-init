# TASK-001 — Seed verified synthetic prerequisite

## Metadata
- Status: done
- Priority: medium
- Owner role: ORCHESTRATOR
- Specs: SPEC-001
- Dependencies: none
- Created: 2026-11-05
- Updated: 2026-11-05

## Objective
Provide one completed, inspectable dependency for the continuity scenario.

## Acceptance criteria
- [x] `evidence/prerequisite.txt` contains exactly `SYNTHETIC-DEPENDENCY-VERIFIED` on one line.

## Completion evidence
| Criterion | Evidence |
| --- | --- |
| 1. Marker file content | `grep -Fx SYNTHETIC-DEPENDENCY-VERIFIED evidence/prerequisite.txt` passed before seeding this dependent task. |

## Blockers
None
