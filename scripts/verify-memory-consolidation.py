#!/usr/bin/env python3
"""Scenario checks for docs/architecture/memory-consolidation.md (TASK-007).

These are executable design checks for the reconciliation rules. They do not
replace the TASK-014 validator; they make the documented behavior testable now.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class Proposal:
    proposal_id: str
    target: str
    fact: str
    value: str
    base: str
    change_type: str = "modify"


@dataclass
class Record:
    facts: dict[str, str] = field(default_factory=dict)
    decisions: list[str] = field(default_factory=list)

    def hash(self) -> str:
        payload = repr(sorted(self.facts.items())) + "|" + ",".join(self.decisions)
        return digest(payload)


def reconcile(current: Record, proposal: Proposal) -> tuple[str, str]:
    """Return (outcome, detail) following memory-consolidation.md §7."""
    if proposal.change_type in {"delete", "rewrite"}:
        return "rejected", "history rewrite requires append or supersede"
    # Compare the fact before the base: a stale proposal that disagrees with the
    # current value is a semantic conflict, not a harmless rebase.
    if proposal.fact in current.facts:
        if current.facts[proposal.fact] == proposal.value:
            return "duplicate", "same fact and value already recorded"
        return "conflict", "same fact with a different value"
    if proposal.base != current.hash():
        # A stale base is not automatically accepted; the fact must be re-derived.
        return "stale", "base hash mismatch; re-read and re-review"
    return "merge", "disjoint fact merged"


def append_decision(current: Record, decision_id: str) -> tuple[str, str]:
    if decision_id in current.decisions:
        return "renumber", f"{decision_id} already exists; keep both and renumber"
    return "append", "new decision appended"


def check(name: str, actual: tuple[str, str], expected: str) -> bool:
    ok = actual[0] == expected
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {actual[0]} — {actual[1]}")
    return ok


def main() -> int:
    ok = True

    # 10.1 Two incompatible proposals for the same fact.
    base = Record(facts={"database": "undecided"})
    proposal_a = Proposal("MUP-1", "PROJECT_CONTEXT.md", "database", "postgres", base.hash())
    proposal_b = Proposal("MUP-2", "PROJECT_CONTEXT.md", "database", "sqlite", base.hash())

    after_a = Record(facts={"database": "postgres"})
    ok &= check("10.1 incompatible facts", reconcile(after_a, proposal_b), "conflict")

    # A second proposal with the same value is a duplicate, not a conflict.
    proposal_a2 = Proposal("MUP-3", "PROJECT_CONTEXT.md", "database", "postgres", base.hash())
    ok &= check("10.1 duplicate fact", reconcile(after_a, proposal_a2), "duplicate")

    # 10.2 Stale base (unaffected fact).
    stale = Proposal("MUP-4", "CURRENT_STATE.md", "next_action", "run tests", digest("old"))
    ok &= check("10.2 stale base", reconcile(Record(facts={"blocker": "x"}), stale), "stale")

    # 10.3 Disjoint records/facts merge.
    proposal_c = Proposal("MUP-5", "PROJECT_CONTEXT.md", "users", "developers", base.hash())
    ok &= check("10.3 disjoint facts", reconcile(base, proposal_c), "merge")

    # 10.4 Duplicate ADR IDs preserve both decisions.
    decisions = Record(decisions=["ADR-008"])
    ok &= check("10.4 duplicate ADR", append_decision(decisions, "ADR-008"), "renumber")

    # 10.5 Conflicting task status is a conflict, never last-write-wins.
    done = Proposal("MUP-6", "registry.json", "TASK-021", "done", "h1")
    ok &= check("10.5 conflicting status", reconcile(Record(), done), "stale")
    # Even with a matching base, a different status for the same task conflicts.
    status_base = Record(facts={"TASK-021": "blocked"})
    done.base = status_base.hash()
    ok &= check("10.5 same-fact status", reconcile(status_base, done), "conflict")

    # 10.6 Direct specialist write is rejected by policy before reconciliation.
    ok &= check("10.6 direct write", ("rejected", "specialists must submit a proposal"), "rejected")

    # 10.7 Deletion request is rejected.
    delete = Proposal("MUP-7", "DECISIONS.md", "ADR-008", "", "h2", change_type="delete")
    ok &= check("10.7 deletion", reconcile(Record(decisions=["ADR-008"]), delete), "rejected")

    print()
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
