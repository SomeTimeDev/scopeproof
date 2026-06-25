from __future__ import annotations

from scopeproof.checks.base import is_project_excluded, result_from_issues
from scopeproof.config import ProjectConfig, TaskConfig
from scopeproof.models import ChangedFile, CheckIssue
from scopeproof.paths import matches_any


def check_scope_escape(
    changed_files: list[ChangedFile],
    config: ProjectConfig,
    task: TaskConfig,
) -> object:
    issues: list[CheckIssue] = []
    for changed in changed_files:
        if is_project_excluded(changed.path, config):
            continue
        if not matches_any(changed.path, config.paths.include):
            issues.append(
                CheckIssue(
                    severity="FAIL",
                    message="Changed file is outside project include paths.",
                    path=changed.path,
                    suggestion=(
                        "Move this change under an included path, or update scopeproof.yml "
                        "if the project scope changed."
                    ),
                    evidence={"include": config.paths.include},
                )
            )
        if matches_any(changed.path, task.forbidden_paths):
            issues.append(
                CheckIssue(
                    severity="FAIL",
                    message="Changed file matches a forbidden task path.",
                    path=changed.path,
                    suggestion=(
                        "Move this change under an allowed extension point, or update "
                        ".scopeproof/task.yml if the scope change is intentional."
                    ),
                    evidence={"forbidden_paths": task.forbidden_paths},
                )
            )
        if task.allowed_paths and not matches_any(changed.path, task.allowed_paths):
            issues.append(
                CheckIssue(
                    severity="FAIL",
                    message="Changed file is outside task allowed_paths.",
                    path=changed.path,
                    suggestion=(
                        "Move this change under an allowed extension point, or update "
                        ".scopeproof/task.yml if the scope change is intentional."
                    ),
                    evidence={"allowed_paths": task.allowed_paths},
                )
            )

    return result_from_issues(
        check_id="scope_escape",
        title="Scope escape",
        pass_summary="Changed files stayed within allowed paths.",
        issue_summary=f"{len(issues)} changed file scope violation(s) detected.",
        issues=issues,
        fail_enabled=config.rules.fail_on_scope_escape,
    )

