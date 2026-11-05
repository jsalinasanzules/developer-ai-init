#!/usr/bin/env python3
"""Preview and safely regenerate the OpenCode adapter's managed files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parent.parent
ADAPTER = ROOT / "adapters" / "opencode"
MANIFEST = ADAPTER / "manifest.json"
START_MARKER = "<!-- BEGIN developer-ai-init managed content"
END_MARKER = "<!-- END developer-ai-init managed content -->"
START_PATTERN = re.compile(
    r"<!-- BEGIN developer-ai-init managed content sha256:([0-9a-f]{64}) -->"
)


@dataclass
class PlannedFile:
    target: pathlib.Path
    relative_target: str
    outcome: str
    reason: str
    content: Optional[str] = None
    overwrite_approved: bool = False


def _mask_jsonc_comments(text: str) -> str:
    """Replace JSONC comments with whitespace while preserving source offsets."""
    chars = list(text)
    i = 0
    in_string = False
    while i < len(text):
        if in_string:
            if text[i] == "\\":
                i += 2
                continue
            if text[i] == '"':
                in_string = False
            i += 1
            continue
        if text[i] == '"':
            in_string = True
            i += 1
            continue
        if text.startswith("//", i):
            end = text.find("\n", i)
            if end < 0:
                end = len(text)
            for pos in range(i, end):
                chars[pos] = " "
            i = end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated JSONC block comment")
            end += 2
            for pos in range(i, end):
                if chars[pos] not in "\r\n":
                    chars[pos] = " "
            i = end
            continue
        i += 1
    return "".join(chars)


def parse_jsonc(text: str):
    masked = _mask_jsonc_comments(text)
    chars = list(masked)
    in_string = False
    i = 0
    while i < len(masked):
        if in_string:
            if masked[i] == "\\":
                i += 2
                continue
            if masked[i] == '"':
                in_string = False
            i += 1
            continue
        if masked[i] == '"':
            in_string = True
            i += 1
            continue
        if masked[i] == ",":
            lookahead = i + 1
            while lookahead < len(masked) and masked[lookahead].isspace():
                lookahead += 1
            if lookahead < len(masked) and masked[lookahead] in "}]":
                chars[i] = " "
        i += 1
    return json.loads("".join(chars))


def _frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated Markdown frontmatter")
    return text[: end + 4], text[end + 5 :]


def _managed_markdown(template: str) -> str:
    header, body = _frontmatter(template)
    managed_body = body.strip()
    digest = hashlib.sha256(managed_body.encode("utf-8")).hexdigest()
    managed = (
        f"{START_MARKER} sha256:{digest} -->\n"
        f"{managed_body}\n{END_MARKER}\n"
    )
    return f"{header}\n{managed}" if header else managed


def _replace_managed_markdown(existing: str, template: str) -> tuple[str, str]:
    generated = _managed_markdown(template)
    if existing == generated:
        return "skip", existing

    template_header, _ = _frontmatter(template)
    start_match = START_PATTERN.search(existing)
    if START_MARKER in existing or END_MARKER in existing:
        if (
            not start_match
            or len(START_PATTERN.findall(existing)) != 1
            or existing.count(END_MARKER) != 1
        ):
            return "conflict", existing
        start = start_match.start()
        end = existing.index(END_MARKER)
        if end < start:
            return "conflict", existing
        current_header, _ = _frontmatter(existing)
        if template_header and current_header != template_header:
            return "conflict", existing
        block_start = start_match.end()
        current_body = existing[block_start:end].strip("\r\n")
        current_digest = hashlib.sha256(current_body.encode("utf-8")).hexdigest()
        block = generated[len(template_header) + (1 if template_header else 0) :]
        end += len(END_MARKER)
        if end < len(existing) and existing[end] == "\n":
            end += 1
        merged = existing[:start] + block + existing[end:]
        if current_digest != start_match.group(1):
            return "conflict", merged
        return ("skip", existing) if merged == existing else ("merge", merged)

    if template_header:
        return "conflict", existing
    if not existing:
        return "merge", generated
    separator = "" if existing.endswith("\n") else "\n"
    return "merge", existing + separator + "\n" + generated


def _root_object_close(masked: str) -> int:
    depth = 0
    in_string = False
    index = 0
    while index < len(masked):
        char = masked[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise ValueError("JSONC root object is not closed")


def _merge_jsonc(existing: str, template: str) -> tuple[str, str]:
    current = parse_jsonc(existing)
    desired = parse_jsonc(template)
    if not isinstance(current, dict) or not isinstance(desired, dict):
        return "conflict", existing

    additions = {}
    for key, value in desired.items():
        if key not in current:
            additions[key] = value
        elif key == "instructions" and value == [] and isinstance(current[key], list):
            continue
        elif current[key] != value:
            return "conflict", existing
    if not additions:
        return "skip", existing

    masked = _mask_jsonc_comments(existing)
    close = _root_object_close(masked)
    before_close = masked[:close]
    last = len(before_close.rstrip()) - 1
    if last < 0 or before_close[last] != "{":
        if before_close[last] != ",":
            comma_at = last + 1
            existing = existing[:comma_at] + "," + existing[comma_at:]
            close += 1

    masked = _mask_jsonc_comments(existing)
    close = _root_object_close(masked)
    before_close = existing[:close]
    whitespace = re.search(r"[ \t\r\n]*$", before_close).group(0)
    body = before_close[: len(before_close) - len(whitespace)] if whitespace else before_close
    indent_match = re.search(r"\n([ \t]+)\S", existing)
    indent = indent_match.group(1) if indent_match else "  "
    fields = ",\n".join(
        f"{indent}{json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in additions.items()
    )
    line_start = existing.rfind("\n", 0, close) + 1
    root_indent = re.match(r"[ \t]*", existing[line_start:close]).group(0)
    merged = (
        body
        + whitespace
        + fields
        + "\n"
        + root_indent
        + existing[close:]
    )
    if parse_jsonc(merged) != {**current, **additions}:
        raise ValueError("internal error: merged JSONC did not preserve its values")
    return "merge", merged


def _safe_relative_path(raw: str) -> pathlib.PurePosixPath:
    path = pathlib.PurePosixPath(raw)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"manifest target must be a safe relative path: {raw}")
    return path


def _destination(root: pathlib.Path, raw: str) -> pathlib.Path:
    relative = _safe_relative_path(raw)
    destination = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"refusing to write through symlink: {raw}")
    resolved_parent = destination.parent.resolve()
    if not resolved_parent.is_relative_to(root):
        raise ValueError(f"target escapes project root: {raw}")
    return destination


def build_plan(
    target_root: pathlib.Path,
    approved_overwrites: Optional[set[str]] = None,
    manifest_path: pathlib.Path = MANIFEST,
) -> list[PlannedFile]:
    root = target_root.resolve(strict=True)
    approved = approved_overwrites or set()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("provider_id") != "opencode":
        raise ValueError("manifest provider_id must be 'opencode'")
    files = manifest.get("generated_files")
    if not isinstance(files, list) or not files:
        raise ValueError("manifest generated_files must be a non-empty array")

    records: list[PlannedFile] = []
    seen_targets = set()
    for entry in files:
        source = (manifest_path.parent / entry["source"]).resolve(strict=True)
        source_root = manifest_path.parent.resolve()
        allowed_source = (
            source.is_relative_to(ROOT)
            if manifest_path.resolve() == MANIFEST.resolve()
            else source.is_relative_to(source_root.parents[1])
        )
        if not allowed_source:
            raise ValueError(f"manifest source escapes repository: {entry['source']}")
        relative = str(_safe_relative_path(entry["target"]))
        if relative in seen_targets:
            raise ValueError(f"duplicate manifest target: {relative}")
        seen_targets.add(relative)
        destination = _destination(root, relative)
        fmt = entry.get("format")
        if fmt not in ("markdown", "jsonc"):
            raise ValueError(f"unsupported format for {relative}: {fmt}")
        template = source.read_text(encoding="utf-8")
        desired = _managed_markdown(template) if fmt == "markdown" else template

        if not destination.exists():
            outcome, content, reason = "create", desired, "target does not exist"
        else:
            if not destination.is_file():
                outcome, content, reason = "conflict", None, "target is not a regular file"
            else:
                existing = destination.read_text(encoding="utf-8")
                if existing == desired:
                    outcome, content, reason = "skip", existing, "already matches template"
                elif fmt == "markdown":
                    outcome, content = _replace_managed_markdown(existing, template)
                    reason = (
                        "managed content updated while preserving surrounding content"
                        if outcome == "merge"
                        else "existing file cannot be safely merged"
                    )
                else:
                    outcome, content = _merge_jsonc(existing, template)
                    reason = (
                        "missing adapter keys merged without replacing user settings"
                        if outcome == "merge"
                        else "conflicting OpenCode setting or already current"
                    )

        is_approved = (
            outcome == "conflict"
            and relative in approved
            and destination.is_file()
            and not destination.is_symlink()
        )
        if outcome == "conflict" and relative in approved and not is_approved:
            reason += "; exact-path approval cannot overwrite a non-regular target"
        if is_approved:
            if fmt != "markdown" or not START_PATTERN.search(content or ""):
                content = desired
            reason += "; exact-path overwrite approved"
        records.append(
            PlannedFile(
                target=destination,
                relative_target=relative,
                outcome=outcome,
                reason=reason,
                content=content,
                overwrite_approved=is_approved,
            )
        )

    unknown_approvals = approved - seen_targets
    if unknown_approvals:
        raise ValueError(
            "overwrite approval must name generated relative paths: "
            + ", ".join(sorted(unknown_approvals))
        )
    return records


def apply_plan(target_root: pathlib.Path, plan: list[PlannedFile]) -> None:
    root = target_root.resolve(strict=True)
    conflicts = [
        item.relative_target
        for item in plan
        if item.outcome == "conflict" and not item.overwrite_approved
    ]
    if conflicts:
        raise ValueError("unapproved conflicts; no files written: " + ", ".join(conflicts))

    for item in plan:
        if item.outcome == "skip":
            continue
        if item.content is None:
            raise ValueError(f"no planned content for {item.relative_target}")
        destination = _destination(root, item.relative_target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not destination.is_file():
            raise ValueError(f"target changed after preview and is not a regular file: {item.relative_target}")
        if destination.exists() and destination.is_symlink():
            raise ValueError(f"target changed to a symlink after preview: {item.relative_target}")
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        )
        try:
            mode = stat.S_IMODE(destination.stat().st_mode) if destination.exists() else 0o644
            with handle:
                handle.write(item.content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(handle.name, mode)
            os.replace(handle.name, destination)
        except Exception:
            try:
                os.unlink(handle.name)
            except FileNotFoundError:
                pass
            raise


def _render_plan(plan: list[PlannedFile]) -> None:
    for item in plan:
        approval = " [APPROVED OVERWRITE]" if item.overwrite_approved else ""
        print(f"{item.outcome.upper():8} {item.relative_target}: {item.reason}{approval}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--dry-run", action="store_true", help="show the plan without writing")
    parser.add_argument(
        "--approve-overwrite",
        action="append",
        default=[],
        metavar="RELATIVE_PATH",
        help="explicitly approve replacing this conflicting generated file (repeatable)",
    )
    args = parser.parse_args(argv)
    try:
        target = args.target.resolve(strict=True)
        if not target.is_dir():
            raise ValueError(f"target is not a directory: {target}")
        plan = build_plan(target, set(args.approve_overwrite))
        _render_plan(plan)
        conflicts = [
            item.relative_target
            for item in plan
            if item.outcome == "conflict" and not item.overwrite_approved
        ]
        if conflicts:
            print("No files written; resolve or explicitly approve the listed conflicts.", file=sys.stderr)
            return 1
        if args.dry_run:
            print("Dry run complete; no files written.")
            return 0
        apply_plan(target, plan)
        print("OpenCode adapter regeneration complete.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
