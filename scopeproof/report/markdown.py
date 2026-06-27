from __future__ import annotations

from scopeproof.models import FullReport


def render_markdown(report: FullReport, verbose: bool = False) -> str:
    diff_target = "staged index" if report.staged else report.head or "working tree"
    lines = [
        "# ScopeProof Report",
        "",
        f"**Overall:** {report.overall_status}  ",
        f"**Project:** {report.project_name or '-'}  ",
        f"**Task:** {report.task_goal or '-'}  ",
        f"**Diff:** {report.base} -> {diff_target}",
        "",
        f"Changed files: {len(report.changed_files)}",
        "",
    ]
    for result in report.results:
        lines.extend([f"## {result.status} {result.check_id}", "", result.summary, ""])
        for issue in result.issues:
            location = ""
            if issue.path:
                location = f"`{issue.path}`"
                if issue.line:
                    location = f"{location}:{issue.line}"
            lines.append(f"- {location} {issue.message}".strip())
            if issue.suggestion:
                lines.append(f"  Suggestion: {issue.suggestion}")
            if verbose and issue.evidence:
                lines.append(f"  Evidence: `{issue.evidence}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
