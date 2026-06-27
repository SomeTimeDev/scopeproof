from __future__ import annotations

from pathlib import Path, PurePosixPath

from scopeproof.checks.base import added_files, is_production_python_file, result_from_issues
from scopeproof.models import ChangedFile, CheckIssue, ImportEdge, Symbol

ENTRYPOINT_NAMES = {"cli.py", "__main__.py", "main.py", "__init__.py"}


def _module_suffixes(path: str) -> list[str]:
    without_suffix = PurePosixPath(path).with_suffix("")
    parts = list(without_suffix.parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    modules = [".".join(parts[index:]) for index in range(len(parts))]
    return [module for module in modules if module]


def _import_references_file(path: str, imports: list[ImportEdge]) -> bool:
    suffixes = _module_suffixes(path)
    for edge in imports:
        if edge.importer_path == path:
            continue
        imported = edge.imported_module.lstrip(".")
        if any(imported == suffix or imported.endswith(f".{suffix}") for suffix in suffixes):
            return True
        if edge.imported_name and edge.imported_name in {suffix.split(".")[-1] for suffix in suffixes}:
            return True
    return False


def _test_references_file(
    repo_root: Path,
    path: str,
    symbols: list[Symbol],
    test_sources: dict[str, str] | None,
) -> bool:
    module_names = {suffix.split(".")[-1] for suffix in _module_suffixes(path)}
    symbol_names = {
        symbol.name
        for symbol in symbols
        if symbol.path == path and symbol.is_public and symbol.kind != "method"
    }
    needles = module_names | symbol_names
    if not needles:
        return False
    if test_sources is None:
        sources = {}
        for test_path in repo_root.rglob("tests/**/*.py"):
            try:
                sources[str(test_path.relative_to(repo_root)).replace("\\", "/")] = (
                    test_path.read_text(encoding="utf-8")
                )
            except UnicodeDecodeError:
                continue
    else:
        sources = {
            source_path: source
            for source_path, source in test_sources.items()
            if source_path.startswith("tests/") and source_path.endswith(".py")
        }
    for source in sources.values():
        if any(needle in source for needle in needles):
            return True
    return False


def check_orphan_new_file(
    changed_files: list[ChangedFile],
    imports: list[ImportEdge],
    current_symbols: list[Symbol],
    repo_root: Path,
    fail_enabled: bool,
    test_sources: dict[str, str] | None = None,
) -> object:
    issues: list[CheckIssue] = []
    for changed in added_files(changed_files):
        if not is_production_python_file(changed.path):
            continue
        if PurePosixPath(changed.path).name in ENTRYPOINT_NAMES:
            continue
        if _import_references_file(changed.path, imports):
            continue
        if _test_references_file(repo_root, changed.path, current_symbols, test_sources):
            continue
        issues.append(
            CheckIssue(
                severity="WARN",
                message="New production Python file is not imported or referenced by tests.",
                path=changed.path,
                suggestion="Wire the file into the package, add tests that use it, or remove it.",
                evidence={"module_suffixes": _module_suffixes(changed.path)},
            )
        )

    return result_from_issues(
        check_id="orphan_new_file",
        title="Orphan new file",
        pass_summary="No orphan new production files detected.",
        issue_summary=f"{len(issues)} orphan new production file(s) detected.",
        issues=issues,
        fail_enabled=fail_enabled,
    )
