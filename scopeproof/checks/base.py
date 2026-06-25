from __future__ import annotations

from pathlib import PurePosixPath

from scopeproof.config import ProjectConfig
from scopeproof.indexer.python_ast import index_python_source
from scopeproof.models import ChangedFile, FAIL, PASS, CheckIssue, CheckResult, Symbol
from scopeproof.paths import matches_any


def result_from_issues(
    *,
    check_id: str,
    title: str,
    pass_summary: str,
    issue_summary: str,
    issues: list[CheckIssue],
    fail_enabled: bool,
) -> CheckResult:
    if not issues:
        return CheckResult(check_id, title, PASS, pass_summary, [])
    severity = FAIL if fail_enabled else "WARN"
    normalized = [
        CheckIssue(
            severity=severity,
            message=issue.message,
            path=issue.path,
            line=issue.line,
            suggestion=issue.suggestion,
            evidence=issue.evidence,
        )
        for issue in issues
    ]
    return CheckResult(check_id, title, severity, issue_summary, normalized)


def is_project_excluded(path: str, config: ProjectConfig) -> bool:
    return matches_any(path, config.paths.exclude)


def is_support_file(path: str) -> bool:
    return (
        path.startswith("tests/")
        or path.startswith("docs/")
        or path == "README.md"
        or path.endswith(".md")
    )


def is_production_python_file(path: str) -> bool:
    name = PurePosixPath(path).name
    return (
        path.endswith(".py")
        and not path.startswith("tests/")
        and not path.startswith("docs/")
        and name not in {"setup.py", "conftest.py", "__init__.py"}
    )


def added_files(changed_files: list[ChangedFile]) -> list[ChangedFile]:
    return [item for item in changed_files if item.status in {"A", "C"}]


def new_public_symbols(
    *,
    changed_files: list[ChangedFile],
    current_symbols: list[Symbol],
    base_symbols: list[Symbol],
    include_tests: bool = True,
) -> list[Symbol]:
    changed_by_path = {item.path: item for item in changed_files if item.path.endswith(".py")}
    base_keys = {
        (symbol.path, symbol.kind, symbol.name, symbol.parent)
        for symbol in base_symbols
        if symbol.is_public
    }
    new_symbols = []
    for symbol in current_symbols:
        changed = changed_by_path.get(symbol.path)
        if changed is None or not symbol.is_public:
            continue
        if not include_tests and symbol.path.startswith("tests/"):
            continue
        if changed.status in {"A", "C"}:
            new_symbols.append(symbol)
            continue
        key = (symbol.path, symbol.kind, symbol.name, symbol.parent)
        if key not in base_keys:
            new_symbols.append(symbol)
    return new_symbols


def base_symbols_for_changed_files(
    changed_files: list[ChangedFile],
    base_sources: dict[str, str],
) -> list[Symbol]:
    symbols: list[Symbol] = []
    for changed in changed_files:
        source = base_sources.get(changed.path)
        if not source or not changed.path.endswith(".py"):
            continue
        file_symbols, _ = index_python_source(source, changed.path)
        symbols.extend(file_symbols)
    return symbols

