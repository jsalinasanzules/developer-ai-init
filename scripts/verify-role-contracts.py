#!/usr/bin/env python3
"""Structural checks for docs/architecture/agent-hierarchy.md (TASK-008).

These checks verify that the role contracts, delegation payload, escalation
rules, sequential fallback, and reusable prompt templates are present and that
the boundary prohibitions are stated. They are review aids, not a substitute for
a conformance harness.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check(name: str, condition: bool) -> bool:
    print(f"{'PASS' if condition else 'FAIL'}  {name}")
    return condition


def main() -> int:
    hierarchy = read("docs/architecture/agent-hierarchy.md")
    orchestrator = read("prompts/orchestrator.md")
    manager = read("prompts/manager.md")
    specialist = read("prompts/specialist.md")
    payload = read("prompts/delegation-payload.md")

    ok = True

    # Invariants B-01..B-10 are defined.
    for i in range(1, 11):
        ok &= check(f"invariant B-{i:02d} present", f"B-{i:02d}" in hierarchy)

    # Delegation payload has every required field.
    for field in [
        "Objective",
        "Context references",
        "Allowed scope",
        "Forbidden changes",
        "Dependencies",
        "Constraints",
        "Expected artifacts",
        "Acceptance criteria",
        "Return format",
        "Escalation",
    ]:
        ok &= check(f"delegation field: {field}", field in payload)

    # Role prohibitions are explicit.
    ok &= check(
        "orchestrator is sole user-facing role",
        "only role that communicates with the user" in orchestrator,
    )
    ok &= check(
        "manager must not ask the user",
        "Do not communicate with the user" in manager,
    )
    ok &= check(
        "specialist must not ask the user",
        "Do not ask the user directly" in specialist,
    )
    ok &= check(
        "specialist must not write canonical memory",
        "Do not write shared canonical records" in specialist,
    )
    ok &= check(
        "manager must not write canonical memory",
        "Do not overwrite canonical memory directly" in manager,
    )

    # Sequential fallback and provider neutrality.
    ok &= check("sequential fallback documented", "## 8. Sequential fallback" in hierarchy)
    ok &= check(
        "no forced parallel delegation",
        "baseline" in hierarchy.lower() and "native delegation is an optimization" in hierarchy,
    )
    ok &= check(
        "provider mapping boundaries documented",
        "## 9. Provider mapping boundaries" in hierarchy,
    )

    # End-to-end sample and review criteria exist.
    ok &= check("end-to-end sample present", "## 11. End-to-end sample delegation" in hierarchy)
    ok &= check("review criteria present", "### 5.3 Review criteria" in hierarchy)

    # The sample enforces the key boundaries.
    sample = hierarchy.split("## 11. End-to-end sample delegation")[1]
    ok &= check("sample: only orchestrator speaks to user", "only the Orchestrator spoke to the user" in sample)
    ok &= check("sample: specialist does not write canonical memory", "did not write canonical memory" in sample)
    ok &= check("sample: manager reviews evidence", "reviews the return" in sample)

    print()
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
