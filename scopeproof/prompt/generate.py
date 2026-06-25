from __future__ import annotations

from scopeproof.config import ExtensionPoint, ProjectConfig, TaskConfig


def matching_extension_points(goal: str, extension_points: list[ExtensionPoint]) -> list[ExtensionPoint]:
    normalized_goal = goal.casefold()
    if not normalized_goal:
        return []
    return [
        point
        for point in extension_points
        if any(keyword.casefold() in normalized_goal for keyword in point.keywords)
    ]


def _section(title: str, items: list[str]) -> list[str]:
    if not items:
        return [f"{title}:", "-", ""]
    return [f"{title}:", *[f"- {item}" for item in items], ""]


def generate_prompt(config: ProjectConfig, task: TaskConfig, goal: str | None = None) -> str:
    task_goal = goal if goal is not None else task.goal
    lines = ["# Task", "", task_goal or "Describe the task before coding.", ""]

    lines.extend(["# Project mission", "", config.project.mission or "-", ""])
    lines.extend(["# Non-goals", ""])
    if config.project.non_goals:
        lines.extend(f"- {item}" for item in config.project.non_goals)
    else:
        lines.append("- Keep changes inside the stated project scope.")
    lines.append("")

    lines.extend(["# Scope constraints", ""])
    lines.extend(_section("Allowed paths", task.allowed_paths))
    lines.extend(_section("Prefer modifying", task.prefer_modify))
    lines.extend(_section("Forbidden paths", task.forbidden_paths))

    relevant = matching_extension_points(task_goal, config.extension_points)
    if relevant:
        lines.extend(["# Relevant extension points", ""])
        for point in relevant:
            lines.append(f"## {point.name}")
            notes = point.notes or [
                "Prefer existing extension points before creating a new module.",
            ]
            lines.extend(f"- {note}" for note in notes)
            if point.prefer_existing_paths:
                lines.append("- Prefer existing paths:")
                lines.extend(f"  - {path}" for path in point.prefer_existing_paths)
            lines.append("")

    lines.extend(_section("Expected behavior", task.expected_behavior))

    verification = task.verification or ["pytest -q", "scopeproof check --base HEAD"]
    lines.extend(["# Before saying done", "", "Run:", "", "```bash"])
    lines.extend(verification)
    if "scopeproof check --base HEAD" not in verification:
        lines.append("scopeproof check --base HEAD")
    lines.extend(["```", ""])
    lines.append("Do not create a new module if an existing function/class can be extended cleanly.")
    return "\n".join(lines).rstrip() + "\n"

