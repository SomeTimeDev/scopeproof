from __future__ import annotations

import ast
from pathlib import Path

from scopeproof.models import ChangedFile, CheckIssue, CheckResult, FAIL, PASS


def check_parse_error(
    changed_files: list[ChangedFile],
    repo_root: Path,
    sources: dict[str, str] | None = None,
) -> CheckResult:
    issues: list[CheckIssue] = []
    for changed in changed_files:
        if not changed.path.endswith(".py") or changed.status == "D":
            continue
        source = sources.get(changed.path) if sources is not None else None
        path = repo_root / changed.path
        if source is None:
            if not path.exists():
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                issues.append(
                    CheckIssue(
                        severity=FAIL,
                        message=f"Could not decode Python file as UTF-8: {exc.reason}",
                        path=changed.path,
                        suggestion="Save the file as UTF-8 or exclude it from Python analysis.",
                    )
                )
                continue
        try:
            ast.parse(source)
        except SyntaxError as exc:
            issues.append(
                CheckIssue(
                    severity=FAIL,
                    message=f"Python syntax error: {exc.msg}",
                    path=changed.path,
                    line=exc.lineno,
                    suggestion="Fix the syntax error before relying on symbol-level checks.",
                    evidence={"offset": exc.offset, "text": exc.text.strip() if exc.text else None},
                )
            )

    if not issues:
        return CheckResult(
            "parse_error",
            "Parse error",
            PASS,
            "Changed Python files parsed successfully.",
            [],
        )
    return CheckResult(
        "parse_error",
        "Parse error",
        FAIL,
        f"{len(issues)} changed Python file(s) could not be parsed.",
        issues,
    )
