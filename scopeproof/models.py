from __future__ import annotations

from dataclasses import dataclass

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


@dataclass(frozen=True)
class ChangedFile:
    path: str
    status: str
    old_path: str | None = None


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    path: str
    line: int
    is_public: bool
    parent: str | None = None


@dataclass(frozen=True)
class ImportEdge:
    importer_path: str
    imported_module: str
    imported_name: str | None
    line: int


@dataclass(frozen=True)
class CheckIssue:
    severity: str
    message: str
    path: str | None = None
    line: int | None = None
    suggestion: str | None = None
    evidence: dict[str, object] | None = None


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    title: str
    status: str
    summary: str
    issues: list[CheckIssue]


@dataclass(frozen=True)
class FullReport:
    project_name: str | None
    task_goal: str | None
    base: str
    head: str | None
    changed_files: list[ChangedFile]
    results: list[CheckResult]

    @property
    def overall_status(self) -> str:
        if any(result.status == FAIL for result in self.results):
            return FAIL
        if any(result.status == WARN for result in self.results):
            return WARN
        return PASS

