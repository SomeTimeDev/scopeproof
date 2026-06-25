from __future__ import annotations

from pathlib import Path

from scopeproof.checks.base import base_symbols_for_changed_files
from scopeproof.checks.duplicate_symbol import check_duplicate_symbol
from scopeproof.checks.module_sprawl import check_module_sprawl
from scopeproof.checks.orphan_new_file import check_orphan_new_file
from scopeproof.checks.public_api_growth import check_public_api_growth
from scopeproof.checks.scope_escape import check_scope_escape
from scopeproof.config import ProjectConfig, TaskConfig
from scopeproof.git import get_changed_files, get_file_at_ref
from scopeproof.indexer.python_ast import index_repo
from scopeproof.models import FullReport


def _base_sources_for_changed_files(
    changed_files: list,
    base: str,
    repo_root: Path,
) -> dict[str, str]:
    sources: dict[str, str] = {}
    for changed in changed_files:
        if not changed.path.endswith(".py") or changed.status == "A":
            continue
        ref_path = changed.old_path if changed.status == "R" and changed.old_path else changed.path
        source = get_file_at_ref(ref_path, base, repo_root)
        if source is not None:
            sources[changed.path] = source
    return sources


def run_checks(
    repo_root: Path,
    config: ProjectConfig,
    task: TaskConfig,
    base: str,
    head: str | None,
) -> FullReport:
    changed_files = get_changed_files(base, head, repo_root)
    current_symbols, imports = index_repo(repo_root, config.paths.include, config.paths.exclude)
    base_sources = _base_sources_for_changed_files(changed_files, base, repo_root)
    base_symbols = base_symbols_for_changed_files(changed_files, base_sources)

    results = [
        check_scope_escape(changed_files, config, task),
        check_module_sprawl(changed_files, config, task),
        check_duplicate_symbol(changed_files, current_symbols, base_symbols, config),
        check_orphan_new_file(
            changed_files,
            imports,
            current_symbols,
            repo_root,
            config.rules.fail_on_orphan_new_file,
        ),
        check_public_api_growth(changed_files, current_symbols, base_symbols, config),
    ]

    return FullReport(
        project_name=config.project.name,
        task_goal=task.goal,
        base=base,
        head=head,
        changed_files=changed_files,
        results=results,
    )

