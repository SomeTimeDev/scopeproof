from __future__ import annotations

import pytest

from scopeproof.config import ConfigError, load_project_config, load_task_config


def test_loads_minimal_config_with_defaults(tmp_path):
    config = tmp_path / "scopeproof.yml"
    config.write_text("version: 1\n", encoding="utf-8")

    loaded = load_project_config(config)

    assert loaded.version == 1
    assert loaded.paths.include == ["**/*"]
    assert loaded.rules.max_new_files_per_task == 3
    assert loaded.rules.fail_on_changed_file_growth is False


def test_loads_full_config(tmp_path):
    config = tmp_path / "scopeproof.yml"
    config.write_text(
        """
version: 1
project:
  name: demo
  mission: test mission
  non_goals: ["no cloud"]
paths:
  include: ["src/**"]
  exclude: [".git/**"]
rules:
  max_new_files_per_task: 1
  fail_on_changed_file_growth: true
extension_points:
  - name: Exporters
    keywords: ["export"]
    notes: ["Extend exporters first."]
""",
        encoding="utf-8",
    )

    loaded = load_project_config(config)

    assert loaded.project.name == "demo"
    assert loaded.project.non_goals == ["no cloud"]
    assert loaded.extension_points[0].name == "Exporters"
    assert loaded.rules.max_new_files_per_task == 1
    assert loaded.rules.fail_on_changed_file_growth is True


def test_missing_task_file_uses_goal_override(tmp_path):
    loaded = load_task_config(tmp_path / ".scopeproof" / "task.yml", goal_override="Add CSV")

    assert loaded.goal == "Add CSV"
    assert loaded.allowed_paths == []


def test_invalid_yaml_raises_clean_error(tmp_path):
    config = tmp_path / "scopeproof.yml"
    config.write_text("version: [", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_project_config(config)
