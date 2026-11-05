#!/usr/bin/env python3
"""Plan and apply an approved Developer AI Init Blueprint installation."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import difflib
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import tempfile
import uuid
from dataclasses import dataclass
from typing import Any, Optional

if __package__:
    from .regenerate_opencode_adapter import build_plan as build_adapter_plan
else:
    from regenerate_opencode_adapter import build_plan as build_adapter_plan

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "blueprint" / "catalog.json"
MANIFEST_RELATIVE = ".blueprint/manifest.json"
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2}))?$")
HAS_DIR_FD = all(
    function in os.supports_dir_fd
    for function in (os.open, os.mkdir, os.stat, os.rename, os.unlink)
)


@dataclass
class PlannedFile:
    target: pathlib.Path
    relative_target: str
    outcome: str
    reason: str
    content: Optional[bytes]
    expected_state: str
    overwrite_approved: bool = False
    is_manifest: bool = False


class GenerationError(ValueError):
    pass


def _today() -> str:
    return dt.date.today().isoformat()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative(raw: str) -> pathlib.PurePosixPath:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw or ":" in raw:
        raise GenerationError(f"unsafe relative path: {raw!r}")
    path = pathlib.PurePosixPath(raw)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
        or any(ord(char) < 32 for char in raw)
    ):
        raise GenerationError(f"unsafe relative path: {raw!r}")
    return path


def _is_symlink_or_reparse_point(path: pathlib.Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    reparse_point_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & reparse_point_attribute
    )


def _state(root: pathlib.Path, relative: str) -> tuple[str, Optional[bytes]]:
    path = _safe_relative(relative)
    cursor = root
    for index, part in enumerate(path.parts):
        cursor = cursor / part
        if _is_symlink_or_reparse_point(cursor):
            return "symlink", None
        if not cursor.exists():
            return "absent", None
        if index < len(path.parts) - 1 and not cursor.is_dir():
            return "not-directory", None
    if cursor.is_dir():
        return "directory", None
    if not cursor.is_file():
        return "not-regular", None
    content = cursor.read_bytes()
    return "file:" + _sha256(content), content


def _catalog() -> dict[str, Any]:
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError(f"cannot read Blueprint catalog: {error}") from error
    version = catalog.get("blueprint_version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise GenerationError("catalog blueprint_version must be semantic version X.Y.Z")
    entries = catalog.get("files")
    if not isinstance(entries, list) or not entries:
        raise GenerationError("catalog files must be a non-empty array")
    targets: set[str] = set()
    folded: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise GenerationError("catalog file entries must be objects")
        target = str(_safe_relative(entry.get("target")))
        if not target.startswith(".blueprint/"):
            raise GenerationError(f"canonical catalog target must be under .blueprint/: {target}")
        if target in targets or target.casefold() in folded:
            raise GenerationError(f"duplicate or case-colliding catalog target: {target}")
        targets.add(target)
        folded.add(target.casefold())
        if entry.get("class") not in ("canonical", "blueprint-managed"):
            raise GenerationError(f"unsupported file class for {target}")
        source = entry.get("source")
        renderer = entry.get("renderer")
        if (isinstance(source, str)) == (isinstance(renderer, str)):
            raise GenerationError(f"{target} must declare exactly one of source or renderer")
        if source is not None:
            source_path = _source_path(source)
            if not source_path.is_file():
                raise GenerationError(f"catalog source is not a file: {source}")
        elif entry.get("format") not in ("json", "markdown"):
            raise GenerationError(f"unsupported format for {target}")
        if entry.get("format") not in ("json", "markdown"):
            raise GenerationError(f"unsupported format for {target}")

    ordered = sorted(targets)
    for index, path in enumerate(ordered):
        if any(other.startswith(path + "/") for other in ordered[index + 1 :]):
            raise GenerationError(f"catalog file path is also a parent directory: {path}")
    return catalog


def _source_path(raw: str) -> pathlib.Path:
    relative = _safe_relative(raw)
    path = ROOT.joinpath(*relative.parts)
    current = ROOT
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise GenerationError(f"catalog source must not traverse symlinks: {raw}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise GenerationError(f"catalog source does not exist: {raw}") from error
    if not resolved.is_relative_to(ROOT):
        raise GenerationError(f"catalog source escapes repository: {raw}")
    return resolved


def _schema_version(name: str) -> str:
    path = ROOT / "schemas" / name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError(f"cannot read schema {name}: {error}") from error
    match = re.search(r":(\d+\.\d+\.\d+):", schema.get("$id", ""))
    version = schema.get("properties", {}).get("schema_version", {}).get("const")
    if not match or match.group(1) != version:
        raise GenerationError(f"inconsistent schema version in {name}")
    return version


def _schema_versions() -> tuple[str, str]:
    manifest_path = ROOT / "schemas" / "manifest.schema.json"
    try:
        manifest_schema = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError(f"cannot read schema manifest.schema.json: {error}") from error
    schema_version = manifest_schema.get("properties", {}).get("schema_version", {}).get("const")
    manifest_version = manifest_schema.get("properties", {}).get("manifest_version", {}).get("const")
    if not isinstance(manifest_version, str) or not SEMVER.fullmatch(manifest_version):
        raise GenerationError("manifest schema has an invalid manifest_version")
    if not isinstance(schema_version, str) or not SEMVER.fullmatch(schema_version):
        raise GenerationError("manifest schema has an invalid schema_version")
    versions = {
        _schema_version(name)
        for name in (
            "project.schema.json",
            "agents.schema.json",
            "memory-metadata.schema.json",
            "task-registry.schema.json",
        )
    }
    if versions != {schema_version}:
        raise GenerationError("canonical schemas do not share one supported schema version")
    return schema_version, manifest_version


def _validate_input(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise GenerationError("confirmed input must be a JSON object")
    expected = {
        "project",
        "purpose",
        "stack",
        "constraints",
        "providers",
        "initialization",
        "context",
        "selected_adapters",
    }
    if set(data) != expected:
        missing = sorted(expected - set(data))
        extra = sorted(set(data) - expected)
        raise GenerationError(f"input fields mismatch; missing={missing}, extra={extra}")

    project = data["project"]
    if not isinstance(project, dict) or not {"name", "slug", "description", "status"} <= set(project):
        raise GenerationError("project requires confirmed name, slug, description, and status")
    allowed_project = {"name", "slug", "description", "status", "repository"}
    if set(project) - allowed_project:
        raise GenerationError("project contains unsupported fields")
    for field in ("name", "slug", "description"):
        if not isinstance(project.get(field), str) or not project[field].strip():
            raise GenerationError(f"project.{field} must be a non-empty confirmed value")
    if not SLUG.fullmatch(project["slug"]):
        raise GenerationError("project.slug must be a lowercase hyphenated identifier")
    if project["status"] not in ("new", "active", "maintenance", "archived"):
        raise GenerationError("project.status is not supported by the project schema")
    if len(project["name"]) > 200 or len(project["slug"]) > 100:
        raise GenerationError("project name or slug exceeds the schema limit")
    if "repository" in project and (
        not isinstance(project["repository"], str) or not project["repository"].strip()
    ):
        raise GenerationError("project.repository must be a non-empty string when supplied")

    purpose = data["purpose"]
    if not isinstance(purpose, dict) or set(purpose) != {"summary", "users", "goals", "non_goals"}:
        raise GenerationError("purpose requires summary, users, goals, and non_goals")
    if not isinstance(purpose["summary"], str) or not purpose["summary"].strip():
        raise GenerationError("purpose.summary must be a non-empty confirmed value")
    for field in ("users", "goals", "non_goals"):
        values = purpose[field]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise GenerationError(f"purpose.{field} must be an array of non-empty strings")
        if len(values) != len(set(values)):
            raise GenerationError(f"purpose.{field} must not contain duplicates")

    if not isinstance(data["stack"], list):
        raise GenerationError("stack must be an array")
    for item in data["stack"]:
        if not isinstance(item, dict) or not {"name", "role"} <= set(item):
            raise GenerationError("each stack item requires name and role")
        if set(item) - {"name", "role", "version", "notes"}:
            raise GenerationError("stack item contains unsupported fields")
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in ("name", "role")):
            raise GenerationError("stack item name and role must be non-empty strings")
        for key in ("version", "notes"):
            if key in item and (not isinstance(item[key], str) or not item[key].strip()):
                raise GenerationError(f"stack item {key} must be non-empty when supplied")

    if not isinstance(data["constraints"], list) or any(
        not isinstance(value, str) or not value.strip() for value in data["constraints"]
    ):
        raise GenerationError("constraints must be an array of non-empty strings")
    if len(data["constraints"]) != len(set(data["constraints"])):
        raise GenerationError("constraints must not contain duplicates")

    if not isinstance(data["providers"], list):
        raise GenerationError("providers must be an array")
    provider_ids: set[str] = set()
    for provider in data["providers"]:
        if not isinstance(provider, dict) or not {"id", "role"} <= set(provider):
            raise GenerationError("each provider requires id and role")
        if set(provider) - {"id", "role", "notes"}:
            raise GenerationError("provider contains unsupported fields")
        provider_id = provider["id"]
        if not isinstance(provider_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", provider_id):
            raise GenerationError("provider id must be a lowercase identifier")
        if provider_id in provider_ids:
            raise GenerationError(f"duplicate provider id: {provider_id}")
        provider_ids.add(provider_id)
        if provider["role"] not in ("primary", "optional", "future"):
            raise GenerationError(f"unsupported role for provider {provider_id}")
        if "notes" in provider and (not isinstance(provider["notes"], str) or not provider["notes"].strip()):
            raise GenerationError(f"provider notes for {provider_id} must be non-empty")

    initialization = data["initialization"]
    if not isinstance(initialization, dict) or set(initialization) != {"status", "unknowns", "assumptions"}:
        raise GenerationError("initialization requires status, unknowns, and assumptions")
    status = initialization["status"]
    unknowns = initialization["unknowns"]
    assumptions = initialization["assumptions"]
    if status not in ("partial", "complete"):
        raise GenerationError("unconfirmed or pending initialization cannot be generated")
    for field, values in (("unknowns", unknowns), ("assumptions", assumptions)):
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise GenerationError(f"initialization.{field} must be an array of non-empty strings")
        if len(values) != len(set(values)):
            raise GenerationError(f"initialization.{field} must not contain duplicates")
    if (status == "complete") != (not unknowns):
        raise GenerationError("initialization status must be complete exactly when unknowns is empty")

    context = data["context"]
    context_fields = {"scope", "domain", "architecture", "conventions"}
    if not isinstance(context, dict) or set(context) != context_fields:
        raise GenerationError("context requires scope, domain, architecture, and conventions")
    if any(not isinstance(value, str) for value in context.values()):
        raise GenerationError("context values must be confirmed strings; use an empty string for unknown")
    if status == "complete" and any(not context.get(field, "").strip() for field in context_fields):
        raise GenerationError("complete initialization requires optional context to be confirmed or explicitly not applicable")

    selected = data["selected_adapters"]
    if not isinstance(selected, list) or any(
        not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", value) for value in selected
    ):
        raise GenerationError("selected_adapters must be an array of adapter identifiers")
    if len(selected) != len(set(selected)):
        raise GenerationError("selected_adapters must not contain duplicates")
    if not set(selected) <= provider_ids:
        raise GenerationError("each selected adapter must also be a confirmed provider")
    return data


def _adapter_details(adapter_id: str) -> tuple[pathlib.Path, str]:
    manifest_path = ROOT / "adapters" / adapter_id / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise GenerationError(f"selected adapter is not available in this Blueprint: {adapter_id}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GenerationError(f"cannot read adapter manifest for {adapter_id}: {error}") from error
    if manifest.get("provider_id") != adapter_id:
        raise GenerationError(f"adapter manifest identity mismatch for {adapter_id}")
    version = manifest.get("adapter_version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise GenerationError(f"adapter manifest has unsupported version for {adapter_id}")
    return manifest_path, version


def _summary_hash(target: pathlib.Path, data: dict[str, Any], classification: str) -> str:
    value = {
        "target": str(target),
        "classification": classification,
        "confirmed_input": data,
    }
    return _sha256(_json_bytes(value))


def _existing_manifest(
    root: pathlib.Path,
    schema_version: str,
    manifest_version: str,
    blueprint_version: str,
) -> Optional[dict[str, Any]]:
    blueprint_dir = root / ".blueprint"
    if not blueprint_dir.exists():
        return None
    if blueprint_dir.is_symlink() or not blueprint_dir.is_dir():
        raise GenerationError(".blueprint exists but is not a safe directory; reconciliation is required")
    relative = MANIFEST_RELATIVE
    state, content = _state(root, relative)
    if not state.startswith("file:") or content is None:
        raise GenerationError(f"{relative} is missing, unsafe, or not a regular file; reconciliation is required")
    try:
        manifest = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GenerationError(f"existing {relative} is invalid; reconciliation is required: {error}") from error
    if not isinstance(manifest, dict):
        raise GenerationError(f"existing {relative} must be an object; reconciliation is required")
    allowed_manifest_fields = {
        "manifest_version",
        "schema_version",
        "blueprint_version",
        "installed_at",
        "files",
        "migrations",
        "notes",
    }
    if set(manifest) - allowed_manifest_fields:
        raise GenerationError(f"existing {relative} has unsupported fields; reconciliation is required")
    required_manifest_fields = {
        "manifest_version",
        "schema_version",
        "blueprint_version",
        "installed_at",
        "files",
    }
    if not required_manifest_fields <= set(manifest):
        raise GenerationError(f"existing {relative} is missing required fields; reconciliation is required")
    versions = {
        "manifest_version": manifest_version,
        "schema_version": schema_version,
        "blueprint_version": blueprint_version,
    }
    for field, expected in versions.items():
        if manifest.get(field) != expected:
            raise GenerationError(
                f"unsupported {field} {manifest.get(field)!r} in {relative}; "
                f"this generator supports {expected}; reconciliation is required"
            )
    if not isinstance(manifest.get("installed_at"), str) or not DATE.fullmatch(manifest["installed_at"]):
        raise GenerationError(f"existing {relative} has invalid installed_at; reconciliation is required")
    if "notes" in manifest and (
        not isinstance(manifest["notes"], str) or not manifest["notes"].strip()
    ):
        raise GenerationError(f"existing {relative} has invalid notes; reconciliation is required")
    migrations = manifest.get("migrations", [])
    if not isinstance(migrations, list):
        raise GenerationError(f"existing {relative} has invalid migrations; reconciliation is required")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise GenerationError(f"existing {relative} has no valid file inventory; reconciliation is required")
    seen: set[str] = set()
    folded: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise GenerationError(f"existing {relative} contains an invalid file record")
        if set(record) - {"path", "class", "sha256", "template_version"}:
            raise GenerationError(f"existing {relative} contains unsupported file-record fields")
        path = str(_safe_relative(record.get("path")))
        if (
            not path.startswith(".blueprint/")
            or path == MANIFEST_RELATIVE
            or ".." in path
            or not re.fullmatch(r"\.blueprint/[A-Za-z0-9._/-]+", path)
        ):
            raise GenerationError(f"existing {relative} has an unsafe inventory path: {path}")
        if path in seen or path.casefold() in folded:
            raise GenerationError(f"existing {relative} has a duplicate inventory path: {path}")
        seen.add(path)
        folded.add(path.casefold())
        if record.get("class") not in ("canonical", "blueprint-managed"):
            raise GenerationError(f"existing {relative} has an unknown file class: {path}")
        if not isinstance(record.get("sha256"), str) or not HEX_SHA256.fullmatch(record["sha256"]):
            raise GenerationError(f"existing {relative} has an invalid hash for {path}")
        if "template_version" in record and (
            not isinstance(record["template_version"], str)
            or not SEMVER.fullmatch(record["template_version"])
        ):
            raise GenerationError(f"existing {relative} has an invalid template version for {path}")
    for migration in migrations:
        if (
            not isinstance(migration, dict)
            or set(migration) - {"from_version", "to_version", "applied_at", "notes"}
            or not isinstance(migration.get("from_version"), str)
            or not SEMVER.fullmatch(migration["from_version"])
            or not isinstance(migration.get("to_version"), str)
            or not SEMVER.fullmatch(migration["to_version"])
            or not isinstance(migration.get("applied_at"), str)
            or not DATE.fullmatch(migration["applied_at"])
            or ("notes" in migration and (
                not isinstance(migration["notes"], str) or not migration["notes"].strip()
            ))
        ):
            raise GenerationError(f"existing {relative} contains an invalid migration record")
    return manifest


def _classify(root: pathlib.Path) -> tuple[str, str]:
    blueprint_dir = root / ".blueprint"
    if blueprint_dir.exists() or blueprint_dir.is_symlink():
        if blueprint_dir.is_symlink() or not blueprint_dir.is_dir():
            return "NEEDS_RECONCILIATION", ".blueprint is not a safe directory"
        manifest = blueprint_dir / "manifest.json"
        if manifest.is_symlink() or not manifest.is_file():
            return "NEEDS_RECONCILIATION", ".blueprint/manifest.json is missing or unsafe"
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return "NEEDS_RECONCILIATION", ".blueprint/manifest.json is unreadable or invalid"
        try:
            schema_version, manifest_version = _schema_versions()
            catalog = _catalog()
            _existing_manifest(root, schema_version, manifest_version, catalog["blueprint_version"])
        except GenerationError as error:
            return "NEEDS_RECONCILIATION", str(error)
        expected = {
            "schema_version": schema_version,
            "manifest_version": manifest_version,
            "blueprint_version": catalog["blueprint_version"],
        }
        if any(value.get(key) != version for key, version in expected.items()):
            return "NEEDS_RECONCILIATION", "existing manifest uses an unsupported version"
        return "ALREADY_INITIALIZED", f"supported Blueprint {catalog['blueprint_version']} manifest found"
    meaningful = [
        item for item in root.iterdir()
        if item.name not in {".git", ".hg", ".svn"}
    ]
    if meaningful:
        return "BROWNFIELD", "existing project content found"
    return "GREENFIELD", "no project content found"


def _stable_json(root: pathlib.Path, relative: str, value: dict[str, Any]) -> bytes:
    now = _today()
    value = copy.deepcopy(value)
    value["updated_at"] = now
    state, current_bytes = _state(root, relative)
    current: Optional[dict[str, Any]] = None
    if state.startswith("file:") and current_bytes is not None:
        try:
            parsed = json.loads(current_bytes.decode("utf-8"))
            if isinstance(parsed, dict):
                current = parsed
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    if current is not None:
        if isinstance(current.get("created_at"), str) and DATE.fullmatch(current["created_at"]):
            value["created_at"] = current["created_at"]
        comparable = copy.deepcopy(value)
        prior = copy.deepcopy(current)
        comparable.pop("updated_at", None)
        prior.pop("updated_at", None)
        if "initialization" in comparable and isinstance(comparable["initialization"], dict):
            comparable["initialization"].pop("completed_at", None)
        if "initialization" in prior and isinstance(prior["initialization"], dict):
            prior["initialization"].pop("completed_at", None)
        if prior == comparable:
            if isinstance(current.get("updated_at"), str) and DATE.fullmatch(current["updated_at"]):
                value["updated_at"] = current["updated_at"]
            if "initialization" in value and isinstance(value["initialization"], dict):
                previous_init = current.get("initialization")
                if (
                    isinstance(previous_init, dict)
                    and isinstance(previous_init.get("completed_at"), str)
                    and DATE.fullmatch(previous_init["completed_at"])
                ):
                    value["initialization"]["completed_at"] = previous_init["completed_at"]
    return _json_bytes(value)


def _render_project(data: dict[str, Any], schema_version: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": schema_version,
        "project": copy.deepcopy(data["project"]),
        "purpose": copy.deepcopy(data["purpose"]),
        "stack": copy.deepcopy(data["stack"]),
        "constraints": list(data["constraints"]),
        "providers": copy.deepcopy(data["providers"]),
        "initialization": {
            "status": data["initialization"]["status"],
            "unknowns": list(data["initialization"]["unknowns"]),
            "assumptions": list(data["initialization"]["assumptions"]),
            "completed_at": _today(),
        },
        "created_at": _today(),
        "updated_at": _today(),
    }
    if "repository" in data["project"]:
        result["project"]["repository"] = data["project"]["repository"]
    return result


def _agents_config(data: dict[str, Any], schema_version: str) -> dict[str, Any]:
    manager_ids = ["manager-architecture", "manager-engineering", "manager-quality", "manager-delivery"]
    roles: dict[str, Any] = {
        "orchestrator": {
            "id": "orchestrator",
            "title": "Orchestrator",
            "kind": "orchestrator",
            "responsibilities": [
                "Own task selection, approval gates, and canonical project records.",
                "Communicate decisions and questions to the user.",
            ],
            "can_delegate_to": manager_ids,
        },
        "managers": [
            {
                "id": manager_id,
                "title": title,
                "kind": "manager",
                "reports_to": "orchestrator",
                "responsibilities": responsibilities,
                "can_delegate_to": ["specialist-engineering", "specialist-testing"],
            }
            for manager_id, title, responsibilities in (
                ("manager-architecture", "Architecture Manager", ["Own bounded architecture analysis and review.", "Surface material decisions to the Orchestrator."]),
                ("manager-engineering", "Engineering Manager", ["Coordinate bounded implementation work.", "Verify implementation evidence before handoff."]),
                ("manager-quality", "Quality Manager", ["Review acceptance evidence and test adequacy.", "Identify regressions and unverified claims."]),
                ("manager-delivery", "Delivery Manager", ["Coordinate task lifecycle and handoffs.", "Keep canonical records consistent."]),
            )
        ],
        "specialists": [
            {
                "id": "specialist-engineering",
                "title": "Engineering Specialist",
                "kind": "specialist",
                "reports_to": "manager-engineering",
                "responsibilities": ["Implement a bounded, approved technical scope.", "Return changes and verification evidence."],
                "can_delegate_to": [],
            },
            {
                "id": "specialist-testing",
                "title": "Testing Specialist",
                "kind": "specialist",
                "reports_to": "manager-quality",
                "responsibilities": ["Create and run bounded behavioral tests.", "Report exact commands and observed results."],
                "can_delegate_to": [],
            },
        ],
    }
    value: dict[str, Any] = {
        "schema_version": schema_version,
        "authority": ["USER", "ORCHESTRATOR", "MANAGERS", "SPECIALISTS"],
        "roles": roles,
        "delegation": {"mode": "sequential", "max_depth": 0, "fallback": "sequential"},
        "approvals": {
            "material_decisions": "user",
            "destructive_actions": "user",
            "conflict_resolution": "user",
        },
        "created_at": _today(),
        "updated_at": _today(),
    }
    if data["selected_adapters"]:
        adapter_id = data["selected_adapters"][0]
        _, version = _adapter_details(adapter_id)
        value["adapter_ref"] = {
            "adapter_id": adapter_id,
            "version": version,
            "notes": "Provider-native files are planned separately from canonical project memory.",
        }
    return value


def _context_file(data: dict[str, Any]) -> str:
    project = data["project"]
    purpose = data["purpose"]
    context = data["context"]
    lines = [
        "# Project Context",
        "",
        f"- Name: {project['name']}",
        f"- Slug: `{project['slug']}`",
        f"- Status: {project['status']}",
        "",
        "## Purpose",
        purpose["summary"],
        "",
        "## Users",
        *([f"- {value}" for value in purpose["users"]] or ["- Not confirmed."]),
        "",
        "## Goals",
        *([f"- {value}" for value in purpose["goals"]] or ["- Not confirmed."]),
        "",
        "## Non-goals",
        *([f"- {value}" for value in purpose["non_goals"]] or ["- Not confirmed."]),
        "",
        "## Confirmed scope",
        context.get("scope") or "Unknown; ask the user before treating a scope as confirmed.",
        "",
        "## Domain",
        context.get("domain") or "Unknown; do not infer domain facts.",
        "",
        "## Constraints",
        *([f"- {value}" for value in data["constraints"]] or ["- None confirmed."]),
        "",
        "## Explicit unknowns",
        *([f"- {value}" for value in data["initialization"]["unknowns"]] or ["- None."]),
        "",
        "## Accepted assumptions",
        *([f"- {value}" for value in data["initialization"]["assumptions"]] or ["- None."]),
        "",
    ]
    return "\n".join(lines)


def _memory_documents(data: dict[str, Any]) -> dict[str, str]:
    context = data["context"]
    architecture = context.get("architecture") or "Not confirmed. Do not infer components, boundaries, or data ownership."
    conventions = context.get("conventions") or "Not confirmed. Inspect evidence and ask before treating conventions as project policy."
    current = (
        "# Current State\n\n"
        "- Stage: project initialization complete.\n"
        "- Active task: none.\n"
        "- Blockers: none recorded.\n"
        "- Pending approvals: none recorded.\n"
        "- Next: confirm the first measurable work items with the user before adding tasks to the registry.\n"
    )
    decisions = (
        "# Decision Log\n\n"
        "No material project decisions have been recorded yet. Append approved decisions; do not rewrite history.\n"
    )
    return {
        ".blueprint/memory/PROJECT_CONTEXT.md": _context_file(data),
        ".blueprint/memory/CURRENT_STATE.md": current,
        ".blueprint/memory/ARCHITECTURE.md": f"# Architecture\n\n{architecture}\n",
        ".blueprint/memory/DECISIONS.md": decisions,
        ".blueprint/memory/CONVENTIONS.md": f"# Conventions\n\n{conventions}\n",
    }


def _metadata(root: pathlib.Path, data: dict[str, Any], memory: dict[str, str], schema_version: str) -> bytes:
    records = []
    for relative, content in memory.items():
        records.append({
            "path": relative,
            "class": "canonical",
            "owner_role": "ORCHESTRATOR",
            "last_updated": _today(),
            "sha256": _sha256(content.encode("utf-8")),
        })
    records.sort(key=lambda item: item["path"])
    state, current_bytes = _state(root, ".blueprint/memory/metadata.json")
    if state.startswith("file:") and current_bytes is not None:
        try:
            old = json.loads(current_bytes.decode("utf-8"))
            old_records = {item.get("path"): item for item in old.get("records", [])}
            for record in records:
                previous = old_records.get(record["path"], {})
                if previous.get("sha256") == record["sha256"] and isinstance(previous.get("last_updated"), str):
                    record["last_updated"] = previous["last_updated"]
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError):
            pass
    value = {
        "schema_version": schema_version,
        "project_id": data["project"]["slug"],
        "updated_at": _today(),
        "records": records,
    }
    old, old_bytes = state, current_bytes
    if old.startswith("file:") and old_bytes is not None:
        try:
            previous = json.loads(old_bytes.decode("utf-8"))
            comparable = copy.deepcopy(value)
            prior = copy.deepcopy(previous)
            prior["updated_at"] = comparable["updated_at"]
            if prior == comparable and isinstance(previous.get("updated_at"), str):
                value["updated_at"] = previous["updated_at"]
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError):
            pass
    return _json_bytes(value)


def _render(entry: dict[str, Any], root: pathlib.Path, data: dict[str, Any], versions: tuple[str, str]) -> bytes:
    target = entry["target"]
    schema_version, _ = versions
    renderer = entry.get("renderer")
    if renderer == "project_config":
        return _stable_json(root, target, _render_project(data, schema_version))
    if renderer == "agents_config":
        return _stable_json(root, target, _agents_config(data, schema_version))
    if renderer == "blueprint_readme":
        text = (
            f"# {data['project']['name']} — Blueprint\n\n"
            f"{data['purpose']['summary']}\n\n"
            f"Blueprint version: `{_catalog()['blueprint_version']}`. "
            "Canonical project memory lives in this directory; this repository's development history is not copied here.\n\n"
            "## Startup order\n"
            "1. Read this file and `manifest.json`.\n"
            "2. Read `config/project.json` and `config/agents.json`.\n"
            "3. Read `memory/PROJECT_CONTEXT.md` and `memory/CURRENT_STATE.md`.\n"
            "4. Select an eligible task from `tasks/registry.json` and read its brief and specifications.\n\n"
            "## Navigation\n"
            "- Memory: `memory/`\n"
            "- Specifications: `specs/README.md`\n"
            "- Task registry and backlog: `tasks/registry.json`, `tasks/backlog.md`\n"
            "- Task briefs: `tasks/items/README.md`\n"
            "- Sessions and handoffs: `sessions/README.md`, `handoffs/README.md`\n"
            "- Schemas: `schemas/`\n"
        )
        return text.encode("utf-8")
    if renderer == "project_context":
        return _memory_documents(data)[target].encode("utf-8")
    if renderer in ("current_state", "architecture", "decisions", "conventions"):
        return _memory_documents(data)[target].encode("utf-8")
    if renderer == "memory_metadata":
        return _metadata(root, data, _memory_documents(data), schema_version)
    if renderer == "specs_readme":
        return (
            "# Specifications\n\n"
            "Store confirmed, project-specific requirements here as `SPEC-<NNN>-<slug>.md`. "
            "Do not copy the Blueprint source repository's development specifications.\n"
        ).encode("utf-8")
    if renderer == "task_registry":
        return _stable_json(root, target, {
            "schema_version": schema_version,
            "updated_at": _today(),
            "tasks": [],
        })
    if renderer == "backlog":
        return (
            "# Product Backlog\n\n"
            "The machine-readable source of task status is `registry.json`. "
            "Add tasks only after scope and measurable acceptance criteria are confirmed.\n"
        ).encode("utf-8")
    if renderer == "task_items_readme":
        return (
            "# Task Briefs\n\n"
            "Store task-specific scope, exclusions, dependencies, acceptance criteria, verification, and evidence here. "
            "The registry is authoritative for task status.\n"
        ).encode("utf-8")
    source = entry.get("source")
    if isinstance(source, str):
        content = _source_path(source).read_bytes()
        if entry["format"] == "json":
            try:
                parsed = json.loads(content.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise GenerationError(f"catalog source is invalid JSON: {source}") from error
            return _json_bytes(parsed)
        return content
    raise GenerationError(f"unknown renderer for {target}: {renderer}")


def _manifest_records(
    catalog: dict[str, Any],
    contents: dict[str, bytes],
) -> list[dict[str, str]]:
    records = []
    for entry in catalog["files"]:
        target = entry["target"]
        record = {
            "path": target,
            "class": entry["class"],
            "sha256": _sha256(contents[target]),
        }
        if entry["class"] == "blueprint-managed":
            record["template_version"] = catalog["blueprint_version"]
        records.append(record)
    return sorted(records, key=lambda record: record["path"])


def _unknown_paths(root: pathlib.Path, known: set[str]) -> list[str]:
    directory = root / ".blueprint"
    if not directory.is_dir() or directory.is_symlink():
        return []
    unknown: list[str] = []
    for current, dirs, files in os.walk(directory, followlinks=False):
        current_path = pathlib.Path(current)
        for name in list(dirs):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                unknown.append(relative)
                dirs.remove(name)
        for name in files:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if relative not in known and relative != MANIFEST_RELATIVE:
                unknown.append(relative)
    return sorted(unknown)


def build_plan(
    target_root: pathlib.Path,
    data: dict[str, Any],
    approved_overwrites: Optional[set[str]] = None,
) -> tuple[str, list[PlannedFile], list[str]]:
    root_arg = pathlib.Path(target_root)
    if root_arg.is_symlink():
        raise GenerationError("target root must not be a symlink")
    try:
        root = root_arg.resolve(strict=True)
    except OSError as error:
        raise GenerationError(f"target does not exist: {target_root}") from error
    if not root.is_dir():
        raise GenerationError(f"target is not a directory: {root}")
    data = _validate_input(data)
    catalog = _catalog()
    schema_version, manifest_version = _schema_versions()
    classification, _ = _classify(root)
    summary_hash = _summary_hash(root, data, classification)
    existing_manifest = _existing_manifest(
        root, schema_version, manifest_version, catalog["blueprint_version"]
    )
    inventory = {
        record["path"]: record["sha256"]
        for record in (existing_manifest or {}).get("files", [])
    }
    approved = set(approved_overwrites or ())
    core_targets = {entry["target"] for entry in catalog["files"]}
    core_targets_folded = {path.casefold(): path for path in core_targets}
    for path in inventory:
        matching = core_targets_folded.get(path.casefold())
        if matching is not None and path != matching:
            raise GenerationError(f"existing manifest path case-collides with catalog target: {path}")
        if path not in core_targets:
            state, _ = _state(root, path)
            if not state.startswith("file:"):
                raise GenerationError(
                    f"unknown manifest path is missing or unsafe: {path}; reconciliation is required"
                )

    adapter_manifests: list[tuple[pathlib.Path, set[str]]] = []
    adapter_targets: set[str] = set()
    adapter_ids = data["selected_adapters"]
    folded_adapter_targets: set[str] = set()
    for adapter_id in adapter_ids:
        adapter_manifest_path, _ = _adapter_details(adapter_id)
        adapter_manifest = json.loads(adapter_manifest_path.read_text(encoding="utf-8"))
        generated_files = adapter_manifest.get("generated_files")
        if not isinstance(generated_files, list) or not generated_files:
            raise GenerationError(f"adapter {adapter_id} has no generated-file catalog")
        targets = set()
        for entry in generated_files:
            if not isinstance(entry, dict) or not isinstance(entry.get("target"), str):
                raise GenerationError(f"adapter {adapter_id} has an invalid destination entry")
            targets.add(str(_safe_relative(entry["target"])))
        folded = {path.casefold() for path in targets}
        if len(folded) != len(targets) or folded & folded_adapter_targets:
            raise GenerationError("selected adapter catalogs contain duplicate or case-colliding destinations")
        folded_adapter_targets |= folded
        adapter_targets |= targets
        adapter_manifests.append((adapter_manifest_path, targets))
    overlap = {path.casefold() for path in core_targets} & folded_adapter_targets
    if overlap:
        raise GenerationError("canonical and provider-adapter catalogs contain colliding destinations")
    all_targets = core_targets | adapter_targets | {MANIFEST_RELATIVE}
    unknown_approvals = approved - all_targets
    if unknown_approvals:
        raise GenerationError("overwrite approval names an unplanned path: " + ", ".join(sorted(unknown_approvals)))

    planned: list[PlannedFile] = []
    desired_contents: dict[str, bytes] = {}
    for entry in catalog["files"]:
        relative = entry["target"]
        desired = _render(entry, root, data, (schema_version, manifest_version))
        desired_contents[relative] = desired
        state, current = _state(root, relative)
        previous_hash = inventory.get(relative)
        approved_path = relative in approved
        outcome = "CONFLICT"
        reason = "existing path is not a regular file"
        if state == "absent":
            if previous_hash is not None:
                reason = "previously managed file is missing; recreation requires exact-path approval"
            else:
                outcome, reason = "CREATE", "destination does not exist"
        elif state.startswith("file:") and current is not None:
            current_hash = _sha256(current)
            if current == desired:
                outcome, reason = "SKIP", "destination already matches confirmed content"
            elif previous_hash is None:
                reason = "untracked content occupies a planned destination"
            elif current_hash == previous_hash:
                outcome, reason = "MERGE", "unchanged managed baseline can be updated"
            else:
                reason = "managed destination differs from its recorded baseline"
        else:
            reason = f"destination is unsafe ({state}) and cannot be overwritten"
        can_approve = state == "absent" or state.startswith("file:")
        is_approved = outcome == "CONFLICT" and approved_path and can_approve
        if is_approved:
            reason += "; exact-path overwrite approved"
        planned.append(PlannedFile(
            target=root.joinpath(*_safe_relative(relative).parts),
            relative_target=relative,
            outcome=outcome,
            reason=reason,
            content=desired,
            expected_state=state,
            overwrite_approved=is_approved,
        ))

    for adapter_manifest_path, targets in adapter_manifests:
        adapter_approvals = approved & targets
        adapter_plan = build_adapter_plan(root, adapter_approvals, adapter_manifest_path)
        for item in adapter_plan:
            state, current = _state(root, item.relative_target)
            content = item.content.encode("utf-8") if item.content is not None else None
            planned.append(PlannedFile(
                target=item.target,
                relative_target=item.relative_target,
                outcome=item.outcome.upper(),
                reason=item.reason,
                content=content,
                expected_state=state,
                overwrite_approved=item.overwrite_approved,
            ))

    used_approvals = {
        item.relative_target for item in planned
        if item.outcome == "CONFLICT" and item.overwrite_approved
    }
    unused = approved - used_approvals
    if unused:
        raise GenerationError(
            "exact-path overwrite approval does not match an unresolved conflict: "
            + ", ".join(sorted(unused))
        )

    manifest_state, manifest_current = _state(root, MANIFEST_RELATIVE)
    unknown = _unknown_paths(root, core_targets)
    unknown.extend(
        path for path in inventory
        if path not in core_targets and path not in unknown
    )
    unknown = sorted(set(unknown))
    nonmanifest = [item for item in planned]
    body = {
        "target": str(root),
        "summary_sha256": summary_hash,
        "catalog_sha256": _sha256(CATALOG.read_bytes()),
        "approved_overwrites": sorted(approved),
        "operations": [
            {
                "path": item.relative_target,
                "outcome": item.outcome,
                "expected_state": item.expected_state,
                "content_sha256": _sha256(item.content) if item.content is not None else None,
                "overwrite_approved": item.overwrite_approved,
            }
            for item in sorted(nonmanifest, key=lambda record: record.relative_target)
        ],
        "manifest_state": manifest_state,
        "preserved_paths": [
            {"path": path, "state": _state(root, path)[0]}
            for path in unknown
        ],
    }
    plan_hash = _sha256(_json_bytes(body))

    existing_files = _manifest_records(catalog, desired_contents)
    existing_unknown_records = [
        record
        for record in (existing_manifest or {}).get("files", [])
        if record["path"] not in core_targets
    ]
    existing_files.extend(copy.deepcopy(existing_unknown_records))
    existing_files.sort(key=lambda record: record["path"])
    notes = []
    if existing_manifest and isinstance(existing_manifest.get("notes"), str) and existing_manifest["notes"].strip():
        notes.append(existing_manifest["notes"].strip())
    changed_non_manifest = any(item.outcome != "SKIP" for item in planned)
    if changed_non_manifest or existing_manifest is None:
        overwrite_note = ", ".join(sorted(approved)) if approved else "none"
        notes.append(
            f"Summary approved by USER via Orchestrator on {_today()}; "
            f"summary_sha256={summary_hash}. Write plan approved by USER via Orchestrator "
            f"on {_today()}; plan_sha256={plan_hash}; approved_overwrite_paths={overwrite_note}."
        )
    manifest: dict[str, Any] = {
        "manifest_version": manifest_version,
        "schema_version": schema_version,
        "blueprint_version": catalog["blueprint_version"],
        "installed_at": (
            existing_manifest["installed_at"]
            if existing_manifest is not None
            else _today()
        ),
        "files": existing_files,
        "migrations": list((existing_manifest or {}).get("migrations", [])),
        "notes": "\n".join(notes) or "No changes; existing approved installation preserved.",
    }
    manifest_content = _json_bytes(manifest)
    if manifest_state == "absent":
        manifest_outcome, manifest_reason = "CREATE", "installation manifest is sealed after verification"
    elif manifest_state.startswith("file:"):
        if manifest_content == manifest_current:
            manifest_outcome, manifest_reason = "SKIP", "manifest already matches the verified installation"
        else:
            manifest_outcome, manifest_reason = "MERGE", "valid installation manifest updated last"
    else:
        manifest_outcome, manifest_reason = "CONFLICT", f"manifest destination is unsafe ({manifest_state})"
    planned.append(PlannedFile(
        target=root / ".blueprint" / "manifest.json",
        relative_target=MANIFEST_RELATIVE,
        outcome=manifest_outcome,
        reason=manifest_reason,
        content=manifest_content,
        expected_state=manifest_state,
        overwrite_approved=False,
        is_manifest=True,
    ))
    return plan_hash, planned, unknown


def _print_summary(target: pathlib.Path, data: dict[str, Any]) -> tuple[str, str]:
    root = target.resolve(strict=True)
    classification, reason = _classify(root)
    digest = _summary_hash(root, data, classification)
    print(f"PROJECT: {data['project']['name']} ({data['project']['slug']})")
    print(f"PURPOSE: {data['purpose']['summary']}")
    print(f"TARGET: {root}")
    print(f"CLASSIFICATION: {classification} — {reason}")
    print(f"INITIALIZATION: {data['initialization']['status']}")
    print("UNKNOWN: " + ("; ".join(data["initialization"]["unknowns"]) or "none"))
    print("SELECTED ADAPTERS: " + (", ".join(data["selected_adapters"]) or "none"))
    print("CONFIRMED INPUT:")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"SUMMARY_SHA256: {digest}")
    print("No files written. The Orchestrator must obtain explicit summary confirmation.")
    return classification, digest


def _render_plan(plan_hash: str, plan: list[PlannedFile], unknown: list[str]) -> None:
    for item in plan:
        approval = " [APPROVED EXACT-PATH OVERWRITE]" if item.overwrite_approved else ""
        print(f"{item.outcome:8} {item.relative_target}: {item.reason}{approval}")
        if item.content is not None:
            print(f"         proposed_sha256={_sha256(item.content)}")
        if item.outcome in ("MERGE", "CONFLICT"):
            relative = _safe_relative(item.relative_target)
            root = item.target.parents[len(relative.parts) - 1]
            state, current = _state(root, item.relative_target)
            if state.startswith("file:") and current is not None and item.content is not None:
                try:
                    old_text = current.decode("utf-8").splitlines(keepends=True)
                    new_text = item.content.decode("utf-8").splitlines(keepends=True)
                    diff = list(difflib.unified_diff(
                        old_text,
                        new_text,
                        fromfile="a/" + item.relative_target,
                        tofile="b/" + item.relative_target,
                    ))
                    if diff:
                        limit = 80
                        print("         " + "".join(diff[:limit]).replace("\n", "\n         ").rstrip())
                        if len(diff) > limit:
                            print(f"         ... diff truncated after {limit} lines")
                except UnicodeDecodeError:
                    print(f"         binary content: current_sha256={_sha256(current)}")
    for path in unknown:
        print(f"PRESERVE  {path}: unknown or untracked Blueprint path; never overwritten")
    print(f"PLAN_SHA256: {plan_hash}")
    print("No files written during preview.")


def _write_atomic_by_path(root: pathlib.Path, relative: str, content: bytes) -> None:
    parts = _safe_relative(relative).parts
    parent = root
    for part in parts[:-1]:
        parent = parent / part
        if _is_symlink_or_reparse_point(parent):
            raise GenerationError(f"refusing to write through symlink or reparse point: {relative}")
        if not parent.exists():
            parent.mkdir()
        if not parent.is_dir():
            raise GenerationError(f"refusing to write through non-directory: {relative}")

    destination = parent / parts[-1]
    if _is_symlink_or_reparse_point(destination):
        raise GenerationError(f"refusing to replace symlink or reparse point: {relative}")
    mode = stat.S_IMODE(destination.stat().st_mode) if destination.exists() else 0o644
    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(handle.name, mode)
        if any(
            _is_symlink_or_reparse_point(root / pathlib.Path(*parts[:index]))
            for index in range(1, len(parts))
        ):
            raise GenerationError(
                f"target path changed to a symlink or reparse point during apply: {relative}"
            )
        if _is_symlink_or_reparse_point(destination):
            raise GenerationError(
                f"target changed to a symlink or reparse point during apply: {relative}"
            )
        os.replace(handle.name, destination)
    except Exception:
        try:
            os.unlink(handle.name)
        except FileNotFoundError:
            pass
        raise


def _write_atomic(root: pathlib.Path, relative: str, content: bytes) -> None:
    if not HAS_DIR_FD:
        _write_atomic_by_path(root, relative, content)
        return
    parts = _safe_relative(relative).parts
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(root, directory_flags)
    temporary_name: Optional[str] = None
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, 0o755, dir_fd=directory_fd)
            except FileExistsError:
                pass
            child_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = child_fd

        filename = parts[-1]
        try:
            existing = os.stat(filename, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            mode = 0o644
        else:
            if not stat.S_ISREG(existing.st_mode):
                raise GenerationError(f"refusing to replace non-regular file: {relative}")
            mode = stat.S_IMODE(existing.st_mode)

        temporary_name = f".{filename}.{uuid.uuid4().hex}.tmp"
        file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(temporary_name, file_flags, mode, dir_fd=directory_fd)
        with os.fdopen(file_fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            filename,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        temporary_name = None
        os.fsync(directory_fd)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)


def apply_plan(root: pathlib.Path, plan: list[PlannedFile]) -> list[str]:
    conflicts = [
        item.relative_target
        for item in plan
        if item.outcome == "CONFLICT" and not item.overwrite_approved
    ]
    if conflicts:
        raise GenerationError("unapproved conflicts; no files written: " + ", ".join(conflicts))

    root = root.resolve(strict=True)
    for item in plan:
        current_state, _ = _state(root, item.relative_target)
        if current_state != item.expected_state:
            raise GenerationError(
                f"target changed after preview; no files written: {item.relative_target}"
            )
    completed: list[str] = []
    ordered = [item for item in plan if not item.is_manifest]
    try:
        for item in ordered:
            if item.outcome == "SKIP":
                continue
            if item.content is None:
                raise GenerationError(f"no planned bytes for {item.relative_target}")
            state, _ = _state(root, item.relative_target)
            if state != item.expected_state:
                raise GenerationError(f"target changed during apply: {item.relative_target}")
            if state in ("symlink", "directory", "not-directory", "not-regular"):
                raise GenerationError(f"unsafe target during apply: {item.relative_target} ({state})")
            _write_atomic(root, item.relative_target, item.content)
            completed.append(item.relative_target)
            if not item.is_manifest:
                written = item.target.read_bytes()
                if _sha256(written) != _sha256(item.content):
                    raise GenerationError(f"post-write verification failed: {item.relative_target}")
        for item in plan:
            if item.is_manifest:
                continue
            if item.content is not None and _state(root, item.relative_target)[0].startswith("file:"):
                if _state(root, item.relative_target)[1] != item.content:
                    raise GenerationError(f"final content verification failed: {item.relative_target}")
        manifest = next(item for item in plan if item.is_manifest)
        if manifest.content is None:
            raise GenerationError("planned manifest has no content")
        value = json.loads(manifest.content.decode("utf-8"))
        for record in value["files"]:
            state, content = _state(root, record["path"])
            if not state.startswith("file:") or content is None or _sha256(content) != record["sha256"]:
                raise GenerationError(f"manifest seal verification failed for {record['path']}")
        if manifest.outcome != "SKIP":
            state, _ = _state(root, manifest.relative_target)
            if state != manifest.expected_state:
                raise GenerationError("manifest changed after preview; manifest was not written")
            _write_atomic(root, manifest.relative_target, manifest.content)
            completed.append(manifest.relative_target)
        return completed
    except (OSError, ValueError, GenerationError) as error:
        pending = [
            item.relative_target for item in plan
            if item.relative_target not in completed and item.outcome != "SKIP"
        ]
        raise GenerationError(
            f"{error}; completed={completed}; pending={pending}; "
            "no rollback attempted; manifest is written only after content verification"
        ) from error


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--input", type=pathlib.Path, required=True, help="confirmed project summary JSON")
    parser.add_argument("--show-summary", action="store_true", help="show the confirmed summary fingerprint")
    parser.add_argument("--confirm-summary", metavar="SHA256", help="confirm the exact summary fingerprint")
    parser.add_argument("--dry-run", action="store_true", help="preview the complete plan without writing")
    parser.add_argument("--approve-plan", metavar="SHA256", help="approve this exact plan fingerprint")
    parser.add_argument(
        "--approve-overwrite",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
        help="single-use approval to replace a conflicting regular file at this exact relative path",
    )
    args = parser.parse_args(argv)
    try:
        if args.show_summary and (
            args.confirm_summary or args.dry_run or args.approve_plan or args.approve_overwrite
        ):
            raise GenerationError("--show-summary cannot be combined with plan or apply approvals")
        if not args.show_summary and not args.confirm_summary:
            raise GenerationError("explicit summary confirmation is required before planning")
        if args.approve_plan and args.dry_run:
            raise GenerationError("--approve-plan applies a plan and cannot be combined with --dry-run")
        if not args.show_summary and not args.dry_run and not args.approve_plan:
            raise GenerationError("apply requires --approve-plan; use --dry-run to preview")
        if args.approve_plan and not HEX_SHA256.fullmatch(args.approve_plan):
            raise GenerationError("--approve-plan must be a SHA-256 plan fingerprint")
        if args.confirm_summary and not HEX_SHA256.fullmatch(args.confirm_summary):
            raise GenerationError("--confirm-summary must be a SHA-256 summary fingerprint")

        target_arg = args.target.expanduser()
        if target_arg.is_symlink():
            raise GenerationError("target root must not be a symlink")
        target = target_arg.resolve(strict=True)
        if not target.is_dir():
            raise GenerationError(f"target is not a directory: {target}")
        try:
            input_data = json.loads(args.input.expanduser().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise GenerationError(f"cannot read confirmed input: {error}") from error
        data = _validate_input(input_data)
        if args.show_summary:
            _print_summary(target, data)
            return 0

        classification, _ = _classify(target)
        actual_summary = _summary_hash(target, data, classification)
        if actual_summary != args.confirm_summary:
            raise GenerationError("summary confirmation is stale or does not match this target and input")
        plan_hash, plan, unknown = build_plan(target, data, set(args.approve_overwrite))
        _render_plan(plan_hash, plan, unknown)
        if any(item.outcome == "CONFLICT" and not item.overwrite_approved for item in plan):
            print("No files written; resolve conflicts and preview again.", file=sys.stderr)
            return 1
        if args.dry_run:
            return 0
        if args.approve_plan != plan_hash:
            raise GenerationError("plan approval is stale or does not match the displayed operations")
        completed = apply_plan(target, plan)
        print(f"Generation complete; verified writes: {', '.join(completed) or 'none'}")
        return 0
    except (OSError, GenerationError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
