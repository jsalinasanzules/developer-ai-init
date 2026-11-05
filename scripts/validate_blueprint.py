#!/usr/bin/env python3
"""Validate Blueprint schemas, records, references, adapters, and secret patterns."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

sys.dont_write_bytecode = True

if __package__:
    from .regenerate_opencode_adapter import parse_jsonc
else:
    from regenerate_opencode_adapter import parse_jsonc

from jsonschema import Draft201909Validator
from jsonschema.exceptions import SchemaError


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
TASK_ID = re.compile(r"^TASK-[0-9]{3}$")
SPEC_ID = re.compile(r"^SPEC-[0-9]{3}$")
STATUS_VALUES = {
    "proposed",
    "ready",
    "in_progress",
    "blocked",
    "in_review",
    "done",
    "cancelled",
}
SCHEMA_FOR_PREFIX = {
    "task-registry": "task-registry.schema.json",
    "memory-metadata": "memory-metadata.schema.json",
    "memory": "memory-metadata.schema.json",
    "project": "project.schema.json",
    "agents": "agents.schema.json",
    "manifest": "manifest.schema.json",
}
LOCAL_DRAFT = "https://json-schema.org/draft/2019-09/schema"
SECRET_ASSIGNMENT = re.compile(
    r"""(?ix)
    \b(api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|
       password|passwd|secret(?:[_-]?key)?)\b
    \s*["']?\s*[:=]\s*
    (?:"([^"\r\n]{12,})"|'([^'\r\n]{12,})'|([^\s,;#}]{12,}))
    """
)
SECRET_TOKEN_PATTERNS = (
    ("AWS access key", re.compile(r"\bAKIA[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)
PLACEHOLDER_VALUES = {
    "changeme",
    "change-me",
    "example",
    "placeholder",
    "redacted",
    "replace-me",
    "your-token",
    "your_api_key",
    "your-secret",
}
SECRET_SCAN_PATHS = (
    "AGENTS.md",
    "README.md",
    "memory",
    "tasks",
    "specs",
    "schemas",
    "adapters/opencode/manifest.json",
    "adapters/opencode/templates",
)


@dataclass(frozen=True)
class Issue:
    severity: str
    path: str
    field: str
    message: str


class Report:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def add(self, severity: str, path: str, field: str, message: str) -> None:
        self.issues.append(Issue(severity, path, field, message))

    def error(self, path: str, field: str, message: str) -> None:
        self.add("ERROR", path, field, message)

    def warning(self, path: str, field: str, message: str) -> None:
        self.add("WARNING", path, field, message)


def _relative(root: pathlib.Path, path: pathlib.Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _safe_segment(value: Any) -> str:
    text = str(value).replace("~", "~0").replace("/", "~1")
    if SECRET_ASSIGNMENT.search(text) or any(pattern.search(text) for _, pattern in SECRET_TOKEN_PATTERNS):
        return "<redacted-key>"
    return text


def _pointer(parts: Iterable[Any]) -> str:
    encoded = [_safe_segment(part) for part in parts]
    return "/" + "/".join(encoded) if encoded else "/"


def _read_json(path: pathlib.Path, root: pathlib.Path, report: Report) -> Optional[Any]:
    relative = _relative(root, path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        report.error(relative, f"line {error.lineno}, column {error.colno}", "invalid JSON syntax")
    except (OSError, UnicodeError):
        report.error(relative, "/", "file cannot be read as UTF-8 JSON")
    return None


def _iter_refs(value: Any, parts: tuple[Any, ...] = ()) -> Iterable[tuple[tuple[Any, ...], Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            next_parts = parts + (key,)
            if key in ("$ref", "$recursiveRef"):
                yield next_parts, child
            yield from _iter_refs(child, next_parts)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_refs(child, parts + (index,))


def _local_refs_only(schema: Any, path: str, report: Report) -> bool:
    local_only = True
    for parts, reference in _iter_refs(schema):
        if not isinstance(reference, str) or not reference.startswith("#"):
            report.error(path, _pointer(parts), "non-local schema references are blocked to guarantee offline validation")
            local_only = False
    return local_only


def _schema_errors(schema: Any) -> list[Any]:
    try:
        Draft201909Validator.check_schema(schema)
    except SchemaError as error:
        return [error]
    return []


def _format_schema_error(
    error: Any,
    path: str,
    report: Report,
    prefix: str = "",
    schema_definition: bool = False,
) -> None:
    if schema_definition:
        error_path = getattr(error, "absolute_schema_path", ())
    else:
        error_path = list(getattr(error, "absolute_path", ()))
        if getattr(error, "validator", None) == "required" and isinstance(
            getattr(error, "instance", None), dict
        ):
            required = getattr(error, "validator_value", [])
            missing = [
                name for name in required
                if isinstance(name, str) and name not in error.instance
            ] if isinstance(required, list) else []
            if missing:
                error_path.append(f"<missing:{_safe_segment(missing[0])}>")
    location = _pointer(error_path)
    keyword = getattr(error, "validator", None)
    keyword_text = f" keyword {keyword!r}" if isinstance(keyword, str) else ""
    field = f"{prefix}{location}" if prefix else location
    report.error(path, field, f"schema validation failed for{keyword_text or ' an unsupported constraint'}")


def _load_schemas(root: pathlib.Path, report: Report) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    schema_dir = root / "schemas"
    if not schema_dir.is_dir():
        report.error("schemas", "/", "schema directory is missing")
        return result
    for path in sorted(schema_dir.glob("*.schema.json")):
        relative = _relative(root, path)
        schema = _read_json(path, root, report)
        if not isinstance(schema, dict):
            report.error(relative, "/", "schema root must be an object")
            continue
        valid_schema = True
        if schema.get("$schema") != LOCAL_DRAFT:
            report.error(relative, "/$schema", "schema must declare JSON Schema Draft 2019-09")
            valid_schema = False
        if not _local_refs_only(schema, relative, report):
            valid_schema = False
        for error in _schema_errors(schema):
            _format_schema_error(error, relative, report, schema_definition=True)
            valid_schema = False
        if valid_schema:
            result[path.name] = schema
    if not result:
        report.error(_relative(root, schema_dir), "/", "no valid Draft 2019-09 schema files were found")
    return result


def _schema_for_fixture(path: pathlib.Path) -> Optional[str]:
    stem = path.name.removesuffix(".json")
    for prefix in sorted(SCHEMA_FOR_PREFIX, key=len, reverse=True):
        if stem == prefix or stem.startswith(prefix + "-"):
            return SCHEMA_FOR_PREFIX[prefix]
    return None


def _validate_instance(
    instance: Any,
    schema: dict[str, Any],
    path: str,
    report: Report,
    field_prefix: str = "",
    emit_errors: bool = True,
) -> list[Any]:
    if not _local_refs_only(schema, path, report):
        return []
    errors = sorted(
        Draft201909Validator(schema).iter_errors(instance),
        key=lambda error: (list(map(str, error.absolute_path)), str(error.validator)),
    )
    if emit_errors:
        for error in errors:
            _format_schema_error(error, path, report, field_prefix)
    return errors


def validate_schemas_and_fixtures(
    root: pathlib.Path,
    report: Report,
    fixtures_only: bool = False,
) -> dict[str, dict[str, Any]]:
    schemas = _load_schemas(root, report)
    if fixtures_only:
        fixture_roots = (root / "schemas" / "fixtures" / "valid", root / "schemas" / "fixtures" / "invalid")
        for fixture_root in fixture_roots:
            if not fixture_root.is_dir():
                report.error(_relative(root, fixture_root), "/", "fixture directory is missing")
                continue
            expected_valid = fixture_root.name == "valid"
            for path in sorted(fixture_root.glob("*.json")):
                relative = _relative(root, path)
                schema_name = _schema_for_fixture(path)
                schema = schemas.get(schema_name or "")
                if schema is None:
                    report.error(relative, "/", "fixture has no matching schema")
                    continue
                instance = _read_json(path, root, report)
                if instance is None:
                    continue
                errors = _validate_instance(
                    instance,
                    schema,
                    relative,
                    report,
                    emit_errors=expected_valid,
                )
                if expected_valid and errors:
                    continue
                if not expected_valid and not errors:
                    report.error(relative, "/", "fixture is expected to be invalid but passes its schema")

    registry_path = root / "tasks" / "registry.json"
    registry_schema = schemas.get("task-registry.schema.json")
    if registry_schema is not None and not fixtures_only:
        registry = _read_json(registry_path, root, report)
        if registry is not None:
            _validate_instance(registry, registry_schema, _relative(root, registry_path), report)
    return schemas


def _metadata(text: str, field: str) -> Optional[str]:
    match = re.search(rf"(?m)^- {re.escape(field)}: (.+?)\s*$", text)
    return match.group(1).strip().strip("`") if match else None


def _brief_title(text: str) -> Optional[str]:
    match = re.search(r"(?m)^# TASK-[0-9]{3} — (.+?)\s*$", text)
    return match.group(1).strip() if match else None


def _csv_metadata(text: str, field: str) -> Optional[list[str]]:
    value = _metadata(text, field)
    if value is None:
        return None
    if value.lower() == "none":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _backlog_status(line: str) -> Optional[str]:
    match = re.match(r"^- \[([ xX])\] \*\*TASK-[0-9]{3}\*\*(?: \(([^)]*)\))?: ", line)
    if not match:
        return None
    if match.group(1).lower() == "x":
        return "done"
    label = (match.group(2) or "").split(",", 1)[0].strip()
    return label if label in STATUS_VALUES else "proposed"


def _validate_records(root: pathlib.Path, report: Report) -> None:
    registry_path = root / "tasks" / "registry.json"
    registry = _read_json(registry_path, root, report)
    if not isinstance(registry, dict) or not isinstance(registry.get("tasks"), list):
        report.error(_relative(root, registry_path), "/tasks", "task registry must contain a tasks array")
        return

    relative_registry = _relative(root, registry_path)
    specs_dir = root / "specs"
    spec_files = {
        match.group(0)
        for path in specs_dir.glob("SPEC-*.md")
        if (match := re.match(r"SPEC-[0-9]{3}", path.stem))
    } if specs_dir.is_dir() else set()
    task_items = root / "tasks" / "items"
    backlog_path = root / "tasks" / "backlog.md"
    try:
        backlog = backlog_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        backlog = ""
        report.error(_relative(root, backlog_path), "/", "backlog is missing or unreadable")

    entries = registry["tasks"]
    indexes: dict[str, int] = {}
    for index, entry in enumerate(entries):
        entry_field = f"/tasks/{index}"
        if not isinstance(entry, dict):
            report.error(relative_registry, entry_field, "task entry must be an object")
            continue
        task_id = entry.get("id")
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            report.error(relative_registry, entry_field + "/id", "task ID must match TASK-NNN")
            continue
        if task_id in indexes:
            report.error(relative_registry, entry_field + "/id", "task ID is duplicated")
            continue
        indexes[task_id] = index

    graph: dict[str, list[str]] = {task_id: [] for task_id in indexes}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("id") not in indexes:
            continue
        task_id = entry["id"]
        field = f"/tasks/{index}"
        specs = entry.get("specs", [])
        if isinstance(specs, list):
            for spec_index, spec_id in enumerate(specs):
                if not isinstance(spec_id, str) or not SPEC_ID.fullmatch(spec_id):
                    report.error(relative_registry, f"{field}/specs/{spec_index}", "spec reference must match SPEC-NNN")
                elif spec_id not in spec_files:
                    report.error(relative_registry, f"{field}/specs/{spec_index}", "referenced specification does not exist")
        dependencies = entry.get("dependencies", [])
        if isinstance(dependencies, list):
            for dependency_index, dependency in enumerate(dependencies):
                dep_field = f"{field}/dependencies/{dependency_index}"
                if dependency == task_id:
                    report.error(relative_registry, dep_field, "task cannot depend on itself")
                elif dependency not in indexes:
                    report.error(relative_registry, dep_field, "referenced task does not exist")
                elif isinstance(dependency, str):
                    graph[task_id].append(dependency)

        brief_path = task_items / f"{task_id}.md"
        try:
            brief = brief_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            report.error(_relative(root, brief_path), "/", "task brief is missing or unreadable")
            continue

        comparisons = (
            ("title", entry.get("title"), _brief_title(brief)),
            ("status", entry.get("status"), _metadata(brief, "Status")),
            ("owner_role", entry.get("owner_role"), _metadata(brief, "Owner role")),
        )
        for field_name, registry_value, brief_value in comparisons:
            if registry_value != brief_value:
                report.error(_relative(root, brief_path), f"/{field_name}", "does not match the task registry")
        brief_specs = _csv_metadata(brief, "Specs")
        if entry.get("specs") != brief_specs:
            report.error(_relative(root, brief_path), "/Specs", "does not match the task registry")
        brief_dependencies = _csv_metadata(brief, "Dependencies")
        if entry.get("dependencies") != brief_dependencies:
            report.error(_relative(root, brief_path), "/Dependencies", "does not match the task registry")

        backlog_matches = [
            line for line in backlog.splitlines()
            if re.search(rf"\*\*{re.escape(task_id)}\*\*", line)
        ]
        if len(backlog_matches) != 1:
            report.error(_relative(root, backlog_path), f"task {task_id}", "must appear exactly once")
        else:
            line = backlog_matches[0]
            backlog_title = re.sub(
                r"^- \[[ xX]\] \*\*TASK-[0-9]{3}\*\*(?: \([^)]+\))?: ",
                "",
                line,
            )
            if not backlog_title.strip():
                report.error(_relative(root, backlog_path), f"task {task_id}", "summary title is empty")
            if _backlog_status(line) != entry.get("status"):
                report.error(_relative(root, backlog_path), f"task {task_id}", "status does not match the task registry")

    colors: dict[str, int] = {}
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(task_id: str, stack: list[str]) -> None:
        color = colors.get(task_id, 0)
        if color == 2:
            return
        if color == 1:
            cycle = tuple(sorted(set(stack[stack.index(task_id):])))
            if cycle not in reported_cycles:
                reported_cycles.add(cycle)
                report.error(relative_registry, f"/tasks/{indexes[task_id]}/dependencies", "dependency graph contains a cycle")
            return
        colors[task_id] = 1
        stack.append(task_id)
        for dependency in graph.get(task_id, []):
            visit(dependency, stack)
        stack.pop()
        colors[task_id] = 2

    for task_id in graph:
        visit(task_id, [])

    state_path = root / "memory" / "CURRENT_STATE.md"
    try:
        current_state = state_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        report.error(_relative(root, state_path), "/", "CURRENT_STATE is missing or unreadable")
        return
    active_tasks = [
        task for task in entries
        if isinstance(task, dict) and task.get("status") in ("in_progress", "in_review")
    ]
    active_section_match = re.search(
        r"(?ms)^## Active task\s*\n(.*?)(?=^## |\Z)", current_state
    )
    active_section = active_section_match.group(1) if active_section_match else ""
    if len(active_tasks) > 1:
        report.error(relative_registry, "/tasks", "more than one task is active")
    elif active_tasks:
        active = active_tasks[0]
        active_id = active.get("id")
        active_status = active.get("status")
        if active_id not in active_section or f"`{active_status}`" not in active_section:
            report.error(_relative(root, state_path), "## Active task", "does not identify the registry's active task")
    elif not re.search(r"(?m)^None\.", active_section):
        report.error(_relative(root, state_path), "## Active task", "must say None when no task is in_progress")


def _safe_relative_path(raw: Any) -> bool:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw or ":" in raw:
        return False
    path = pathlib.PurePosixPath(raw)
    return not path.is_absolute() and all(part not in ("", ".", "..") for part in path.parts)


def _validate_adapter(root: pathlib.Path, report: Report) -> None:
    manifest_path = root / "adapters" / "opencode" / "manifest.json"
    relative_manifest = _relative(root, manifest_path)
    manifest = _read_json(manifest_path, root, report)
    if not isinstance(manifest, dict):
        report.error(relative_manifest, "/", "adapter manifest root must be an object")
        return
    if not isinstance(manifest.get("provider_id"), str) or not isinstance(manifest.get("adapter_version"), str):
        report.error(relative_manifest, "/", "provider_id and adapter_version strings are required")
    files = manifest.get("generated_files")
    if not isinstance(files, list):
        report.error(relative_manifest, "/generated_files", "must be an array")
        return

    adapter_root = manifest_path.parent.resolve()
    seen_targets: set[str] = set()
    for index, entry in enumerate(files):
        field = f"/generated_files/{index}"
        if not isinstance(entry, dict):
            report.error(relative_manifest, field, "entry must be an object")
            continue
        source = entry.get("source")
        target = entry.get("target")
        fmt = entry.get("format")
        if not _safe_relative_path(source):
            report.error(relative_manifest, field + "/source", "source must be a safe relative path")
            continue
        source_path = manifest_path.parent / pathlib.PurePosixPath(source)
        try:
            resolved_source = source_path.resolve(strict=True)
        except OSError:
            report.error(relative_manifest, field + "/source", "source file does not exist")
            continue
        if not resolved_source.is_relative_to(adapter_root) or not resolved_source.is_file():
            report.error(relative_manifest, field + "/source", "source must be a regular file inside the adapter")
        if not _safe_relative_path(target):
            report.error(relative_manifest, field + "/target", "target must be a safe relative path")
        elif target.casefold() in seen_targets:
            report.error(relative_manifest, field + "/target", "target path is duplicated or case-colliding")
        else:
            seen_targets.add(target.casefold())
        if fmt not in ("markdown", "jsonc"):
            report.error(relative_manifest, field + "/format", "format must be markdown or jsonc")
        if fmt == "jsonc" and resolved_source.is_file():
            try:
                config = parse_jsonc(resolved_source.read_text(encoding="utf-8"))
                if not isinstance(config, dict):
                    report.error(_relative(root, resolved_source), "/", "JSONC root must be an object")
            except json.JSONDecodeError as error:
                report.error(
                    _relative(root, resolved_source),
                    f"line {error.lineno}, column {error.colno}",
                    "invalid JSONC syntax",
                )
            except (OSError, UnicodeError, ValueError):
                report.error(_relative(root, resolved_source), "/", "invalid or unreadable JSONC configuration")


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered in PLACEHOLDER_VALUES
        or lowered.startswith(("your-", "your_", "<", "${", "replace-", "example"))
        or set(lowered) <= {"x", "*", "-", "_"}
    )


def _scan_paths(root: pathlib.Path) -> list[pathlib.Path]:
    files: set[pathlib.Path] = set()
    for name in SECRET_SCAN_PATHS:
        candidate = root / name
        if candidate.is_file() and not candidate.is_symlink():
            files.add(candidate)
        elif candidate.is_dir() and not candidate.is_symlink():
            for current, dirs, names in os.walk(candidate, followlinks=False):
                current_path = pathlib.Path(current)
                dirs[:] = [
                    directory for directory in dirs
                    if not (current_path / directory).is_symlink()
                ]
                files.update(
                    current_path / filename for filename in names
                    if not (current_path / filename).is_symlink()
                )
    return sorted(files)


def _scan_secrets(root: pathlib.Path, report: Report) -> None:
    for path in _scan_paths(root):
        relative = _relative(root, path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            report.warning(relative, "/", "file was not scanned as UTF-8 text")
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            assignment = SECRET_ASSIGNMENT.search(line)
            if assignment:
                candidate = next((value for value in assignment.groups()[1:] if value), "")
                if candidate and not _is_placeholder(candidate):
                    report.error(relative, f"line {line_number} / credential field", "possible secret-like value detected; value redacted")
            for label, pattern in SECRET_TOKEN_PATTERNS:
                if pattern.search(line):
                    report.error(relative, f"line {line_number}", f"possible {label} detected; value redacted")


def validate(root: pathlib.Path, fixtures_only: bool = False) -> Report:
    report = Report()
    root = root.resolve(strict=True)
    schemas = validate_schemas_and_fixtures(root, report, fixtures_only)
    if not fixtures_only:
        _validate_records(root, report)
        _validate_adapter(root, report)
        _scan_secrets(root, report)
    return report


def _print_report(report: Report) -> None:
    for issue in sorted(report.issues, key=lambda item: (item.path, item.field, item.severity, item.message)):
        print(f"{issue.severity} {issue.path}:{issue.field}: {issue.message}")
    errors = sum(issue.severity == "ERROR" for issue in report.issues)
    warnings = sum(issue.severity == "WARNING" for issue in report.issues)
    print(f"Validation: {errors} error(s), {warnings} warning(s)")
    if errors == 0:
        print("RESULT: PASS")
    else:
        print("RESULT: FAIL")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, default=ROOT)
    parser.add_argument(
        "--fixtures-only",
        action="store_true",
        help="validate schema definitions and valid/invalid schema fixtures only",
    )
    args = parser.parse_args(argv)
    try:
        report = validate(args.root, fixtures_only=args.fixtures_only)
    except OSError as error:
        print(f"ERROR {args.root}:/: cannot access validation root ({type(error).__name__})")
        return 2
    _print_report(report)
    return 0 if not any(issue.severity == "ERROR" for issue in report.issues) else 1


if __name__ == "__main__":
    raise SystemExit(main())
