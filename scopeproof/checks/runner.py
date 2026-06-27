from __future__ import annotations

from pathlib import Path

from scopeproof.checks.base import base_symbols_for_changed_files
from scopeproof.checks.changed_file_growth import check_changed_file_growth
from scopeproof.checks.duplicate_symbol import check_duplicate_symbol
from scopeproof.checks.module_sprawl import check_module_sprawl
from scopeproof.checks.orphan_new_file import check_orphan_new_file
from scopeproof.checks.parse_error import check_parse_error
from scopeproof.checks.public_api_growth import check_public_api_growth
from scopeproof.checks.scope_escape import check_scope_escape
from scopeproof.config import ProjectConfig, TaskConfig
from scopeproof.git import get_changed_files, get_file_at_index, get_file_at_ref, list_tracked_files
from scopeproof.indexer.python_ast import index_python_source, index_repo
from scopeproof.models import FullReport
from scopeproof.paths import filter_included


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


def _staged_sources(
    repo_root: Path,
    config: ProjectConfig,
    apply_path_filters: bool = True,
) -> dict[str, str]:
    selected = [path for path in list_tracked_files(repo_root) if path.endswith(".py")]
    if apply_path_filters:
        selected = filter_included(selected, config.paths.include, config.paths.exclude)
    sources = {}
    for path in selected:
        source = get_file_at_index(path, repo_root)
        if source is not None:
            sources[path] = source
    return sources


def _index_sources(sources: dict[str, str]):
    symbols = []
    imports = []
    for path, source in sources.items():
        file_symbols, file_imports = index_python_source(source, path)
        symbols.extend(file_symbols)
        imports.extend(file_imports)
    return symbols, imports


def run_checks(
    repo_root: Path,
    config: ProjectConfig,
    task: TaskConfig,
    base: str,
    head: str | None,
    staged: bool = False,
) -> FullReport:
    changed_files = get_changed_files(base, head, repo_root, staged=staged)
    current_sources = _staged_sources(repo_root, config) if staged else None
    parse_sources = (
        _staged_sources(repo_root, config, apply_path_filters=False) if staged else None
    )
    parse_result = check_parse_error(changed_files, repo_root, sources=parse_sources)
    current_symbols, imports = (
        _index_sources(current_sources)
        if current_sources is not None
        else index_repo(repo_root, config.paths.include, config.paths.exclude)
    )
    base_sources = _base_sources_for_changed_files(changed_files, base, repo_root)
    base_symbols = base_symbols_for_changed_files(changed_files, base_sources)

    results = [
        check_scope_escape(changed_files, config, task),
        check_changed_file_growth(changed_files, config),
        check_module_sprawl(changed_files, config, task),
        parse_result,
        check_duplicate_symbol(changed_files, current_symbols, base_symbols, config),
        check_orphan_new_file(
            changed_files,
            imports,
            current_symbols,
            repo_root,
            config.rules.fail_on_orphan_new_file,
            test_sources=current_sources,
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
        staged=staged,
    )
