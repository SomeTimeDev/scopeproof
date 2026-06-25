from __future__ import annotations

from scopeproof.config import ExtensionPoint, ProjectConfig, ProjectInfo, TaskConfig
from scopeproof.prompt.generate import generate_prompt


def test_prompt_generate_includes_scope_and_extension_point():
    config = ProjectConfig(
        project=ProjectInfo(
            mission="A CLI for exporting structured data.",
            non_goals=["Do not add cloud sync."],
        ),
        extension_points=[
            ExtensionPoint(
                name="Exporters",
                keywords=["csv", "export"],
                notes=["Prefer extending exporters."],
            )
        ],
    )
    task = TaskConfig(
        goal="Add CSV export support",
        allowed_paths=["src/**/exporters/**"],
        forbidden_paths=["src/**/services/**"],
        verification=["pytest -q"],
    )

    rendered = generate_prompt(config, task)

    assert "# Task" in rendered
    assert "Add CSV export support" in rendered
    assert "Prefer extending exporters." in rendered
    assert "scopeproof check --base HEAD" in rendered

