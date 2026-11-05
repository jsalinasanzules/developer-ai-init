#!/usr/bin/env python3
"""Structural checks for OpenCode adapter templates and workflows (TASK-009/010).

Verifies template completeness, JSONC validity, frontmatter shape against the
OpenCode V2 conventions inspected 2026-11-04, canonical-path discipline, and
the absence of secrets. Workflow checks cover required startup, task, and handoff
protocol steps. These are review aids; the full conformance harness is TASK-014.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADAPTER = ROOT / "adapters" / "opencode" / "templates"

REQUIRED_AGENT_FILES = {
    "orchestrator.md": "primary",
    "manager-architecture.md": "subagent",
    "manager-engineering.md": "subagent",
    "manager-quality.md": "subagent",
    "manager-delivery.md": "subagent",
    "specialist.md": "subagent",
}
REQUIRED_COMMANDS = [
    "blueprint-startup.md",
    "blueprint-next.md",
    "blueprint-task.md",
    "blueprint-handoff.md",
    "blueprint-consolidate.md",
]
WORKFLOW_REQUIREMENTS = {
    "blueprint-startup.md": [
        ".blueprint/README.md",
        ".blueprint/manifest.json",
        ".blueprint/config/project.json",
        ".blueprint/config/agents.json",
        ".blueprint/memory/PROJECT_CONTEXT.md",
        ".blueprint/memory/CURRENT_STATE.md",
        ".blueprint/tasks/registry.json",
        "active task brief",
        "linked specifications",
        "version is unknown",
        "handoff",
        "context packet",
    ],
    "blueprint-next.md": [
        "in_progress",
        "ready",
        "dependencies",
        "completion evidence",
        "registry status",
        "status matches the registry entry",
        "wait for user confirmation",
    ],
    "blueprint-task.md": [
        "in_progress",
        "in_review",
        "completion evidence",
        "source-only completion gate",
        "installed in generated projects",
        "every recorded test command",
        "current_state.md",
        "sequential fallback",
        "material decision",
        "checked",
        "blockers",
    ],
    "blueprint-handoff.md": [
        "repository state",
        "working-tree status",
        "acceptance-criterion evidence",
        "cold-start checklist",
        "current files and git",
        "current_state.md",
    ],
    "blueprint-consolidate.md": [
        "owning record",
        "content hash",
        "concurrent changes semantically",
        "conflicting values",
        "no secrets",
    ],
}
# V2 allows: description, mode, model, permissions, steps, hidden, disabled, color,
# request. V1 deprecated fields must be absent (opencode.ai/v2/docs/agents).
AGENT_V1_FORBIDDEN = ["tools", "temperature", "top_p", "prompt", "permission",
                      "disable", "maxSteps"]
# Markdown command frontmatter allows: description, agent, model, subagent (the
# body is the template). `template` in frontmatter is forbidden.
COMMAND_FRONTMATTER_FIELDS = ["description", "agent", "model", "subagent", "subtask"]

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9+/]{16,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
]


def simple_yaml_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if text.startswith("---\n"):
        head, _, body = text.partition("\n---\n")
        if not _:
            raise ValueError("unterminated frontmatter")
        fields = {}
        for line in head.split("\n")[1:]:
            if not line.strip() or line.strip().startswith("#"):
                continue
            key, _, value = line.partition(":")
            fields.setdefault(key.strip(), value.strip())
        return fields, body
    return {}, text


def parse_jsonc(text: str):
    # Strip // comments (the template uses no block comments on that syntax).
    out, in_string = [], False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return json.loads("".join(out))


def main() -> int:
    ok = True

    def check(name: str, cond: bool) -> None:
        nonlocal ok
        print(f"{'PASS' if cond else 'FAIL'}  {name}")
        ok &= bool(cond)

    check("opencode.jsonc present", (ADAPTER / "opencode.jsonc").exists())
    check("AGENTS-TARGET.md present", (ADAPTER / "AGENTS-TARGET.md").exists())

    manifest_path = ADAPTER.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    generated = manifest.get("generated_files", [])
    targets = [entry.get("target") for entry in generated]
    check("adapter manifest present", manifest.get("provider_id") == "opencode")
    check("adapter manifest targets are unique", len(targets) == len(set(targets)))
    check(
        "generated adapter does not install Python files",
        not any(str(target).endswith(".py") for target in targets),
    )
    check(
        "source completion gate remains internal",
        (ROOT / "scripts" / "task_lifecycle.py").is_file()
        and not any("task_lifecycle.py" in str(target) for target in targets),
    )
    manifest_sources_valid = all(
        (ADAPTER.parent / entry.get("source", "")).resolve().is_file()
        and (ADAPTER.parent / entry.get("source", "")).resolve().is_relative_to(ROOT)
        for entry in generated
    )
    check("adapter manifest sources exist within the repository", manifest_sources_valid)
    generated_sources = [
        (ADAPTER.parent / entry.get("source", "")).resolve()
        for entry in generated
        if (ADAPTER.parent / entry.get("source", "")).resolve().is_file()
    ]
    check(
        "generated templates do not invoke Python",
        all(
            not re.search(
                r"(?:^|\s)python(?:3)?\s+(?:scripts/|\.blueprint/)",
                source.read_text().lower(),
            )
            for source in generated_sources
        ),
    )
    check(
        "regeneration and lifecycle behavioral tests present",
        (ROOT / "tests" / "test_opencode_regeneration.py").is_file()
        and (ROOT / "tests" / "test_task_lifecycle.py").is_file(),
    )

    agent_ids = set()
    for fname, mode in REQUIRED_AGENT_FILES.items():
        path = ADAPTER / "agents" / fname
        if not path.exists():
            check(f"agent file present: {fname}", False)
            continue
        fields, body = simple_yaml_frontmatter(path.read_text())
        check(f"agent {fname}: description present", "description" in fields)
        check(f"agent {fname}: mode is {mode}", fields.get("mode") == mode)
        check(f"agent {fname}: body is non-empty system prompt", len(body.strip()) > 100)
        for f in AGENT_V1_FORBIDDEN:
            if f in fields:
                check(f"agent {fname}: no V1 field {f}", False)
        check(
            f"agent {fname}: manager/specialist does not address user",
            "user-facing" not in body.lower() or fname == "orchestrator.md",
        )
        if fname != "orchestrator.md":
            forbidden = (
                "escalate to the orchestrator" in body.lower()
                and "never communicate with the user" in body.lower()
            )
            check(f"agent {fname}: escalation + no-user-contact stated", forbidden)
        agent_ids.add(path.stem)

    for fname in REQUIRED_COMMANDS:
        path = ADAPTER / "commands" / fname
        if not path.exists():
            check(f"command file present: {fname}", False)
            continue
        fields, body = simple_yaml_frontmatter(path.read_text())
        unexpected = [f for f in fields if f not in COMMAND_FRONTMATTER_FIELDS]
        check(f"command {fname}: frontmatter fields valid", not unexpected)
        check(f"command {fname}: body acts as template", len(body.strip()) > 100)
        agent = fields.get("agent")
        check(f"command {fname}: agent reference valid", agent in agent_ids)
        if fname in WORKFLOW_REQUIREMENTS:
            lowered = body.lower()
            for requirement in WORKFLOW_REQUIREMENTS[fname]:
                check(
                    f"command {fname}: workflow includes {requirement}",
                    requirement.lower() in lowered,
                )

    target_instructions = (ADAPTER / "AGENTS-TARGET.md").read_text().lower()
    for requirement in (
        ".blueprint/manifest.json",
        ".blueprint/config/agents.json",
        ".blueprint/memory/project_context.md",
        ".blueprint/memory/current_state.md",
        ".blueprint/tasks/registry.json",
        "linked specs",
        "stop on missing required records",
    ):
        check(
            f"AGENTS-TARGET.md: startup includes {requirement}",
            requirement.lower() in target_instructions,
        )

    config = (ADAPTER / "opencode.jsonc").read_text()
    data = parse_jsonc(config)
    check("opencode.jsonc parses as JSONC", isinstance(data, dict))
    check("default_agent is orchestrator", data.get("default_agent") == "orchestrator")
    check(
        "schema reference present",
        data.get("$schema") == "https://opencode.ai/config.json",
    )
    check(
        "depth-2 opt-in is commented out",
        '"experimental"' in config and parse_jsonc(config).get("experimental") is None,
    )

    for path in ADAPTER.rglob("*"):
        if path.is_file():
            text = path.read_text()
            bad = []
            for patt in SECRET_PATTERNS:
                if patt.search(text):
                    bad.append("secrets")
                    break
            # Canonical basenames must always be referenced under `.blueprint/`.
            for m in re.finditer(
                r"(?<!\.blueprint/)(?<![\w/.])(memory|tasks|specs|handoffs|sessions|config)/([A-Za-z0-9._/-]+)",
                text,
            ):
                snippet = m.group(0)
                if "/.blueprint/" in text[max(0, m.start() - 1) : m.end()] or text[: m.start()].endswith(".blueprint/"):
                    continue
                bad.append(f"non-canonical path reference: {snippet[:60]}")
            if bad:
                check(f"{path.name}: canonical-path discipline ({bad})", False)
    print()
    print(f"RESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
