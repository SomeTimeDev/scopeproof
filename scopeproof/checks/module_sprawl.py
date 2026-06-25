from __future__ import annotations

from pathlib import PurePosixPath

from scopeproof.checks.base import (
    added_files,
    is_production_python_file,
    is_project_excluded,
    result_from_issues,
)
from scopeproof.config import ExtensionPoint, ProjectConfig, TaskConfig
from scopeproof.models import ChangedFile, CheckIssue
from scopeproof.paths import matches_any

SUSPICIOUS_MODULE_WORDS = (
    "service",
    "manager",
    "helper",
    "utils",
    "util",
    "new",
    "v2",
    "legacy",
)


def _matching_extension_points(goal: str, extension_points: list[ExtensionPoint]) -> list[ExtensionPoint]:
    normalized_goal = goal.casefold()
    if not normalized_goal:
        return []
    return [
        point
        for point in extension_points
        if any(keyword.casefold() in normalized_goal for keyword in point.keywords)
    ]


def _has_changed_adr(changed_files: list[ChangedFile], config: ProjectConfig) -> bool:
    return any(matches_any(changed.path, config.rules.adr_paths) for changed in changed_files)


def _is_suspicious_module(path: str) -> bool:
    name = PurePosixPath(path).stem.casefold()
    return any(word in name for word in SUSPICIOUS_MODULE_WORDS)


def _is_modify_only(task: TaskConfig) -> bool:
    if task.expected_change_type and task.expected_change_type.casefold() in {
        "modify-only",
        "modify_only",
    }:
        return True
    return any("modify-only" in item.casefold() for item in task.expected_behavior)


def check_module_sprawl(
    changed_files: list[ChangedFile],
    config: ProjectConfig,
    task: TaskConfig,
) -> object:
    issues: list[CheckIssue] = []
    relevant_changed = [
        changed for changed in changed_files if not is_project_excluded(changed.path, config)
    ]
    added = added_files(relevant_changed)
    production_added = [
        changed for changed in added if is_production_python_file(changed.path)
    ]

    if len(added) > config.rules.max_new_files_per_task:
        issues.append(
            CheckIssue(
                severity="WARN",
                message=(
                    f"This task added {len(added)} files; configured limit is "
                    f"{config.rules.max_new_files_per_task}."
                ),
                suggestion="Reduce new file count or split the task into smaller changes.",
                evidence={"added_files": [item.path for item in added]},
            )
        )

    matched_points = _matching_extension_points(task.goal, config.extension_points)
    modify_only = _is_modify_only(task)
    for point in matched_points:
        for changed in production_added:
            allowed_under_extension = not point.allow_new_files_under or matches_any(
                changed.path,
                point.allow_new_files_under,
            )
            if not allowed_under_extension:
                issues.append(
                    CheckIssue(
                        severity="WARN",
                        message=(
                            f'New file {changed.path} was added, but task goal matches '
                            f'extension point "{point.name}".'
                        ),
                        path=changed.path,
                        suggestion=(
                            "Extend the existing extension point unless this new module is "
                            "intentional. If intentional, add an ADR under docs/adr/."
                        ),
                        evidence={
                            "extension_point": point.name,
                            "allow_new_files_under": point.allow_new_files_under,
                        },
                    )
                )
            if point.prefer_existing_paths and task.prefer_modify and (
                modify_only or not allowed_under_extension
            ):
                issues.append(
                    CheckIssue(
                        severity="WARN",
                        message=(
                            f'New production module was added while extension point "{point.name}" '
                            "has preferred files to modify."
                        ),
                        path=changed.path,
                        suggestion="Prefer extending the existing interface before creating a new module.",
                        evidence={
                            "prefer_existing_paths": point.prefer_existing_paths,
                            "prefer_modify": task.prefer_modify,
                            "modify_only": modify_only,
                        },
                    )
                )

    has_adr = _has_changed_adr(relevant_changed, config)
    for changed in production_added:
        if _is_suspicious_module(changed.path) and not has_adr:
            issues.append(
                CheckIssue(
                    severity="WARN",
                    message="Suspicious new production module name added without an ADR.",
                    path=changed.path,
                    suggestion=(
                        "Extend an existing abstraction, rename the module to its concrete role, "
                        "or add an ADR if the new abstraction is intentional."
                    ),
                    evidence={"suspicious_words": list(SUSPICIOUS_MODULE_WORDS)},
                )
            )

    if config.rules.require_adr_for_new_module and production_added and not has_adr:
        issues.append(
            CheckIssue(
                severity="WARN",
                message="A new production module was added but no ADR changed.",
                suggestion="Add an ADR under the configured ADR paths if this module is intentional.",
                evidence={"adr_paths": config.rules.adr_paths},
            )
        )

    return result_from_issues(
        check_id="module_sprawl",
        title="Module sprawl",
        pass_summary="No module sprawl detected.",
        issue_summary=f"{len(issues)} potential needless module/new-file issue(s) detected.",
        issues=issues,
        fail_enabled=config.rules.fail_on_module_sprawl,
    )
