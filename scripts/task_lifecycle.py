#!/usr/bin/env python3
"""Validate task evidence before synchronizing an in_review task to done."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shlex
import subprocess
import stat
import sys
import tempfile
from datetime import date
from typing import Optional


def _section(text: str, title: str) -> str:
    match = re.search(
        rf"^##[ \t]+{re.escape(title)}[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _metadata(task_text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:[ \t]*(.*?)\s*$", task_text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _table_rows(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _cells(line)
        if cells and all(re.fullmatch(r"[-: ]+", cell or " ") for cell in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def _local_link_paths(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\((?!https?://|mailto:)([^)#]+)(?:#[^)]*)?\)", text)


def _resolve_reference(root: pathlib.Path, task_path: pathlib.Path, raw: str) -> Optional[pathlib.Path]:
    reference = pathlib.Path(raw)
    if reference.is_absolute():
        return None
    resolved = (task_path.parent / reference).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        return None
    return resolved


def _status_in_section(current_state: str, task_id: str) -> bool:
    active = _section(current_state, "Active task")
    return task_id in active and re.search(r"\bin_review\b", active) is not None


def validate_completion(
    root: pathlib.Path,
    task_id: str,
    review_path: Optional[pathlib.Path],
) -> list[str]:
    errors: list[str] = []
    if not re.fullmatch(r"TASK-\d{3}", task_id):
        return [f"invalid task ID: {task_id}"]
    root = root.resolve(strict=True)
    blueprint_root = root / ".blueprint" if (root / ".blueprint").is_dir() else root
    registry_path = blueprint_root / "tasks" / "registry.json"
    task_path = blueprint_root / "tasks" / "items" / f"{task_id}.md"
    backlog_path = blueprint_root / "tasks" / "backlog.md"
    state_path = blueprint_root / "memory" / "CURRENT_STATE.md"
    if review_path is not None and not review_path.is_absolute():
        review_path = root / review_path
    for path in (registry_path, task_path, backlog_path, state_path):
        if not path.is_file():
            errors.append(f"required canonical record is missing: {path.relative_to(root)}")
    if errors:
        return errors


    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read task registry: {error}"]
    if not isinstance(registry, dict) or not isinstance(registry.get("tasks"), list):
        return ["task registry must contain a tasks array"]
    task_text = task_path.read_text(encoding="utf-8")
    backlog = backlog_path.read_text(encoding="utf-8")
    current_state = state_path.read_text(encoding="utf-8")
    entries = [
        item
        for item in registry["tasks"]
        if isinstance(item, dict) and item.get("id") == task_id
    ]
    if len(entries) != 1:
        return [f"registry must contain exactly one entry for {task_id}"]
    entry = entries[0]
    title_match = re.search(r"^# " + re.escape(task_id) + r" — (.+?)\s*$", task_text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    if not title or entry.get("title") != title:
        errors.append("registry and task brief titles do not agree")
    if entry.get("status") != "in_review" or _metadata(task_text, "Status").strip("`") != "in_review":
        errors.append("registry and task brief must both be in_review")
    if entry.get("owner_role") != _metadata(task_text, "Owner role"):
        errors.append("registry and task brief owner roles do not agree")
    specs = [item.strip() for item in _metadata(task_text, "Specs").split(",") if item.strip()]
    dependencies_raw = _metadata(task_text, "Dependencies")
    dependencies = (
        [item.strip() for item in dependencies_raw.split(",") if item.strip()]
        if dependencies_raw.lower() != "none"
        else []
    )
    if entry.get("specs") != specs:
        errors.append("registry and task brief specifications do not agree")
    if entry.get("dependencies") != dependencies:
        errors.append("registry and task brief dependencies do not agree")

    backlog_rows = [
        line
        for line in backlog.splitlines()
        if re.search(rf"\*\*{re.escape(task_id)}\*\*", line)
    ]
    expected_backlog = rf"^- \[ \] \*\*{re.escape(task_id)}\*\* \(in_review(?:, [^)]+)?\): {re.escape(title)}\.(?: Depends on .+)?\s*$"
    if len(backlog_rows) != 1 or not re.fullmatch(expected_backlog, backlog_rows[0]):
        errors.append("backlog projection must contain one matching unchecked in_review row")
    if not _status_in_section(current_state, task_id):
        errors.append("CURRENT_STATE must identify this task as the in_review active task")

    criteria = []
    for match in re.finditer(r"^- \[([ xX])\] (.+?)\s*$", _section(task_text, "Acceptance criteria"), re.MULTILINE):
        criteria.append((match.group(1).lower() == "x", match.group(2).strip()))
    if not criteria:
        errors.append("task brief has no acceptance criteria")
    elif any(not checked for checked, _ in criteria):
        errors.append("every acceptance criterion must be checked before completion")

    evidence_rows = _table_rows(_section(task_text, "Completion evidence"))
    if evidence_rows and evidence_rows[0][0].lower() == "criterion":
        evidence_rows = evidence_rows[1:]
    evidence_by_id = {}
    for row in evidence_rows:
        if len(row) >= 3:
            if row[0] in evidence_by_id:
                errors.append(f"completion evidence contains duplicate {row[0]}")
            evidence_by_id[row[0]] = (row[1], row[2])
    if len(evidence_rows) != len(criteria) or len(evidence_by_id) != len(criteria):
        errors.append("completion evidence must contain exactly one row per acceptance criterion")
    for index, (_, criterion) in enumerate(criteria, start=1):
        criterion_id = f"AC-{index:02d}"
        row = evidence_by_id.get(criterion_id)
        if not row:
            errors.append(f"completion evidence is missing {criterion_id}")
            continue
        mapped_criterion, evidence = row
        if mapped_criterion != criterion:
            errors.append(f"{criterion_id} evidence does not map to the exact acceptance criterion")
        links = _local_link_paths(evidence)
        test_paths = [
            resolved
            for path in links
            if (resolved := _resolve_reference(root, task_path, path))
            and "tests" in resolved.relative_to(root).parts
        ]
        test_name = re.search(r"\btest_[A-Za-z0-9_]+\b", evidence)
        if not test_paths or not test_name or not any(
            test_name.group(0) in path.read_text(encoding="utf-8") for path in test_paths
        ):
            errors.append(f"{criterion_id} requires a concrete, named behavioral test reference")

    verification_rows = _table_rows(_section(task_text, "Verification results"))
    if verification_rows and verification_rows[0][0].lower() in ("check", "test"):
        verification_rows = verification_rows[1:]
    if not verification_rows:
        errors.append("verification results must record at least one passing test command")
    for row in verification_rows:
        if len(row) < 4 or row[2].upper() != "PASS":
            errors.append("every required verification command must have a PASS result")
            continue
        command_match = re.search(r"`([^`]+)`", row[1])
        report_links = _local_link_paths(row[3])
        report_path = (
            _resolve_reference(root, task_path, report_links[0]) if report_links else None
        )
        if not command_match or report_path is None:
            errors.append("verification rows require an exact command and an existing report link")
            continue
        report = report_path.read_text(encoding="utf-8")
        if "RESULT: PASS" not in report or command_match.group(1) not in report:
            errors.append(f"verification report does not prove PASS for {command_match.group(1)}")

    review_section = _section(task_text, "Manager review")
    review_reference_match = re.search(r"`([^`]+)`", review_section)
    if review_path is None or not review_path.is_file():
        errors.append("an existing independent Manager review artifact is required")
    else:
        review_resolved = review_path.resolve()
        if not review_resolved.is_relative_to(root):
            errors.append("Manager review artifact must be inside the project root")
        elif not review_reference_match or pathlib.Path(review_reference_match.group(1)).as_posix() != review_resolved.relative_to(root).as_posix():
            errors.append("task brief must reference the supplied Manager review artifact")
        else:
            review_text = review_resolved.read_text(encoding="utf-8")
            if f"Task: {task_id}" not in review_text:
                errors.append("Manager review artifact names a different task")
            reviewer_match = re.search(
                r"^Reviewer role:[ \t]*(.*?)\s*$", review_text, re.MULTILINE
            )
            if not reviewer_match or not re.fullmatch(
                r"MANAGER: [A-Za-z][A-Za-z0-9 /&-]*", reviewer_match.group(1)
            ):
                errors.append("review must be performed by an appropriate Manager")
            if "Decision: APPROVED" not in review_text:
                errors.append("Manager review must explicitly approve the evidence")
            if "Independent review: YES" not in review_text:
                errors.append("Manager review artifact must identify an independent review")
    return errors


def run_verification_commands(
    root: pathlib.Path,
    task_id: str,
) -> tuple[list[str], list[tuple[str, str]]]:
    root = root.resolve(strict=True)
    blueprint_root = root / ".blueprint" if (root / ".blueprint").is_dir() else root
    task_path = blueprint_root / "tasks" / "items" / f"{task_id}.md"
    if not task_path.is_file():
        return [f"task brief is missing: {task_path}"], []
    rows = _table_rows(_section(task_path.read_text(encoding="utf-8"), "Verification results"))
    if rows and rows[0][0].lower() in ("check", "test"):
        rows = rows[1:]
    if not rows:
        return ["verification results must record at least one passing test command"], []

    errors = []
    outputs = []
    for row in rows:
        if len(row) < 4 or row[2].upper() != "PASS":
            errors.append("every required verification command must be recorded as PASS")
            continue
        command_match = re.search(r"`([^`]+)`", row[1])
        if not command_match:
            errors.append("verification command must be enclosed in backticks")
            continue
        command = command_match.group(1)
        try:
            argv = shlex.split(command)
            if not argv:
                errors.append("verification command cannot be empty")
                continue
            result = subprocess.run(
                argv,
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired, ValueError) as error:
            errors.append(f"verification command failed to execute ({command}): {error}")
            continue
        output = (result.stdout or "") + (result.stderr or "")
        outputs.append((command, output))
        if result.returncode != 0:
            errors.append(f"verification command exited {result.returncode}: {command}")
    return errors, outputs


def _replace_section(text: str, title: str, replacement: str) -> str:
    pattern = re.compile(
        rf"(^##[ \t]+{re.escape(title)}[ \t]*\r?\n).*?(?=^##[ \t]+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if not pattern.search(text):
        raise ValueError(f"missing ## {title} section")
    return pattern.sub(lambda match: match.group(1) + replacement.rstrip() + "\n\n", text, count=1)


def _append_to_section(text: str, title: str, addition: str) -> str:
    if not re.search(rf"^##[ \t]+{re.escape(title)}[ \t]*$", text, re.MULTILINE):
        return text
    content = _section(text, title)
    return _replace_section(text, title, f"{content}\n{addition}")


def _atomic_write(changes: dict[pathlib.Path, str]) -> None:
    staged: dict[pathlib.Path, str] = {}
    originals = {path: path.read_bytes() for path in changes}
    replaced: list[pathlib.Path] = []
    try:
        for path, content in changes.items():
            if path.is_symlink():
                raise ValueError(f"refusing to update canonical symlink: {path}")
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            )
            staged[path] = handle.name
            with handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(handle.name, stat.S_IMODE(path.stat().st_mode))
        for path, temporary in staged.items():
            os.replace(temporary, path)
            replaced.append(path)
    except Exception:
        rollback_errors = []
        for path in reversed(replaced):
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=path.parent,
                    prefix=f".{path.name}.rollback.",
                    suffix=".tmp",
                    delete=False,
                ) as handle:
                    handle.write(originals[path])
                    handle.flush()
                    os.fsync(handle.fileno())
                    rollback = handle.name
                os.chmod(rollback, stat.S_IMODE(path.stat().st_mode))
                os.replace(rollback, path)
            except Exception as rollback_error:
                rollback_errors.append(f"{path}: {rollback_error}")
        if rollback_errors:
            raise RuntimeError("update failed and rollback was incomplete: " + "; ".join(rollback_errors))
        raise
    finally:
        for temporary in staged.values():
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def complete_task(
    root: pathlib.Path,
    task_id: str,
    review_path: pathlib.Path,
    next_action: str,
    today: Optional[str] = None,
) -> list[tuple[str, str]]:
    root = root.resolve(strict=True)
    blueprint_root = root / ".blueprint" if (root / ".blueprint").is_dir() else root
    registry_path = blueprint_root / "tasks" / "registry.json"
    task_path = blueprint_root / "tasks" / "items" / f"{task_id}.md"
    backlog_path = blueprint_root / "tasks" / "backlog.md"
    state_path = blueprint_root / "memory" / "CURRENT_STATE.md"
    if not review_path.is_absolute():
        review_path = root / review_path
    errors = validate_completion(root, task_id, review_path)
    if errors:
        raise ValueError("; ".join(errors))
    verification_errors, outputs = run_verification_commands(root, task_id)
    if verification_errors:
        raise ValueError("; ".join(verification_errors))
    errors = validate_completion(root, task_id, review_path)
    if errors:
        raise ValueError("; ".join(errors))
    today = today or date.today().isoformat()

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entry = next(item for item in registry["tasks"] if item["id"] == task_id)
    entry["status"] = "done"
    entry["next_action"] = next_action
    registry["updated_at"] = today

    task_text = task_path.read_text(encoding="utf-8")
    task_text = re.sub(r"(?m)^- Status: in_review$", "- Status: done", task_text, count=1)
    task_text = re.sub(r"(?m)^- Updated: .+$", f"- Updated: {today}", task_text, count=1)
    task_text = _replace_section(task_text, "Next action", next_action)

    backlog = backlog_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"(?m)^- \[ \] \*\*{re.escape(task_id)}\*\* \(in_review(?:, [^)]+)?\): ")
    if len(pattern.findall(backlog)) != 1:
        raise ValueError("backlog changed after validation; expected one in_review row")
    backlog = pattern.sub(f"- [x] **{task_id}** (done): ", backlog, count=1)

    state = state_path.read_text(encoding="utf-8")
    state = _replace_section(
        state,
        "Active task",
        f"None. {task_id} is complete; see `{review_path.resolve().relative_to(root).as_posix()}`.",
    )
    state = _append_to_section(
        state,
        "Completed recently",
        f"- **{task_id}** (`done`): evidence gate approved the acceptance evidence and synchronized task records; Manager review `{review_path.resolve().relative_to(root).as_posix()}`.",
    )
    state = _replace_section(state, "Next", next_action)

    _atomic_write(
        {
            registry_path: json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
            task_path: task_text,
            backlog_path: backlog,
            state_path: state,
        }
    )
    return outputs


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "complete"):
        sub = subparsers.add_parser(command)
        sub.add_argument("task_id")
        sub.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())
        sub.add_argument("--review", type=pathlib.Path, required=True)
        if command == "complete":
            sub.add_argument("--next-action", required=True)
            sub.add_argument("--apply", action="store_true", help="persist the verified transition")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        review = args.review if args.review.is_absolute() else root / args.review
        if args.command == "check" or (args.command == "complete" and not args.apply):
            errors = validate_completion(root, args.task_id, review)
            if errors:
                for error in errors:
                    print(f"BLOCKED: {error}", file=sys.stderr)
                return 1
            verification_errors, outputs = run_verification_commands(root, args.task_id)
            for command, output in outputs:
                print(f"TEST OUTPUT: {command}\n{output.rstrip()}")
            if verification_errors:
                for error in verification_errors:
                    print(f"BLOCKED: {error}", file=sys.stderr)
                return 1
        if args.command == "complete" and args.apply:
            outputs = complete_task(root, args.task_id, review, args.next_action)
            for command, output in outputs:
                print(f"TEST OUTPUT: {command}\n{output.rstrip()}")
            print(f"COMPLETED: {args.task_id} is now synchronized as done.")
            return 0
        print(f"PASS: completion gate accepted {args.task_id}; evidence and canonical records agree.")
        if args.command == "complete":
            print("No files written; rerun with --apply to persist the transition.")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
