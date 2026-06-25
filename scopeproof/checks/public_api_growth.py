from __future__ import annotations

from scopeproof.checks.base import new_public_symbols, result_from_issues
from scopeproof.config import ProjectConfig
from scopeproof.models import ChangedFile, CheckIssue, Symbol


def check_public_api_growth(
    changed_files: list[ChangedFile],
    current_symbols: list[Symbol],
    base_symbols: list[Symbol],
    config: ProjectConfig,
) -> object:
    new_symbols = new_public_symbols(
        changed_files=changed_files,
        current_symbols=current_symbols,
        base_symbols=base_symbols,
        include_tests=False,
    )
    issues: list[CheckIssue] = []
    limit = config.rules.max_new_public_symbols_per_task
    if len(new_symbols) > limit:
        issues.append(
            CheckIssue(
                severity="WARN",
                message=f"This task added {len(new_symbols)} public symbols; configured limit is {limit}.",
                suggestion=(
                    "Reduce public API growth. Prefer private helpers, extend existing abstractions, "
                    "or split the task into smaller changes."
                ),
                evidence={"new_symbols": [f"{symbol.path}::{symbol.name}" for symbol in new_symbols]},
            )
        )

    return result_from_issues(
        check_id="public_api_growth",
        title="Public API growth",
        pass_summary="Public API growth is within the configured limit.",
        issue_summary=f"{len(issues)} public API growth issue(s) detected.",
        issues=issues,
        fail_enabled=config.rules.fail_on_public_api_growth,
    )

