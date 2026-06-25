from __future__ import annotations

from scopeproof.models import FullReport


def render_console(report: FullReport, verbose: bool = False) -> str:
    added = sum(1 for item in report.changed_files if item.status in {"A", "C"})
    lines = [
        "ScopeProof Report",
        "",
        f"Project: {report.project_name or '-'}",
        f"Task: {report.task_goal or '-'}",
        f"Diff: {report.base} -> {report.head or 'working tree'}",
        "",
        f"Changed files: {len(report.changed_files)}",
        f"Added files: {added}",
        "",
    ]
    for result in report.results:
        lines.append(f"{result.status} {result.check_id}")
        lines.append(f"  {result.summary}")
        for issue in result.issues:
            location = ""
            if issue.path:
                location = f"{issue.path}"
                if issue.line:
                    location = f"{location}:{issue.line}"
                location = f"{location}: "
            lines.append(f"  {location}{issue.message}")
            if issue.suggestion:
                lines.append(f"  Suggestion: {issue.suggestion}")
            if verbose and issue.evidence:
                lines.append(f"  Evidence: {issue.evidence}")
        lines.append("")
    lines.append(f"Overall: {report.overall_status}")
    return "\n".join(lines).rstrip() + "\n"

