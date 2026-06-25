from __future__ import annotations

from scopeproof.checks.base import is_project_excluded, result_from_issues
from scopeproof.config import ProjectConfig
from scopeproof.models import ChangedFile, CheckIssue


def check_changed_file_growth(
    changed_files: list[ChangedFile],
    config: ProjectConfig,
) -> object:
    counted_files = [
        changed for changed in changed_files if not is_project_excluded(changed.path, config)
    ]
    limit = config.rules.max_changed_files_per_task
    issues: list[CheckIssue] = []
    if len(counted_files) > limit:
        issues.append(
            CheckIssue(
                severity="WARN",
                message=f"This task changed {len(counted_files)} files; configured limit is {limit}.",
                suggestion="Reduce file churn, or split the task into smaller focused changes.",
                evidence={"changed_files": [item.path for item in counted_files]},
            )
        )

    return result_from_issues(
        check_id="changed_file_growth",
        title="Changed file growth",
        pass_summary="Changed file count is within the configured limit.",
        issue_summary=f"{len(issues)} changed-file growth issue(s) detected.",
        issues=issues,
        fail_enabled=config.rules.fail_on_changed_file_growth,
    )

