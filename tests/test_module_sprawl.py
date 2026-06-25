from __future__ import annotations

from scopeproof.checks.module_sprawl import check_module_sprawl
from scopeproof.config import ExtensionPoint, ProjectConfig, RuleConfig, TaskConfig
from scopeproof.models import FAIL, PASS, ChangedFile


def test_module_sprawl_flags_extension_point_escape():
    config = ProjectConfig(
        rules=RuleConfig(max_new_files_per_task=3, fail_on_module_sprawl=True),
        extension_points=[
            ExtensionPoint(
                name="Exporters",
                keywords=["export", "csv"],
                prefer_existing_paths=["src/**/exporters/**"],
                allow_new_files_under=["src/**/exporters/**", "tests/**"],
            )
        ],
    )
    task = TaskConfig(goal="Add CSV export support", prefer_modify=["src/demo/exporters/base.py"])

    result = check_module_sprawl(
        [ChangedFile("src/demo/services/csv_export_service.py", "A")],
        config,
        task,
    )

    assert result.status == FAIL
    assert any("Exporters" in issue.message for issue in result.issues)


def test_module_sprawl_does_not_flag_support_files():
    config = ProjectConfig(rules=RuleConfig(max_new_files_per_task=3))
    task = TaskConfig(goal="Update docs")

    result = check_module_sprawl(
        [ChangedFile("tests/test_csv.py", "A"), ChangedFile("docs/export.md", "A")],
        config,
        task,
    )

    assert result.status == PASS


def test_module_sprawl_allows_new_file_under_matched_extension_path():
    config = ProjectConfig(
        rules=RuleConfig(max_new_files_per_task=3, fail_on_module_sprawl=True),
        extension_points=[
            ExtensionPoint(
                name="Exporters",
                keywords=["export", "csv"],
                prefer_existing_paths=["src/**/exporters/**"],
                allow_new_files_under=["src/**/exporters/**", "tests/**"],
            )
        ],
    )
    task = TaskConfig(goal="Add CSV export support", prefer_modify=["src/demo/exporters/base.py"])

    result = check_module_sprawl(
        [ChangedFile("src/demo/exporters/csv.py", "A")],
        config,
        task,
    )

    assert result.status == PASS


def test_module_sprawl_flags_allowed_new_file_when_task_is_modify_only():
    config = ProjectConfig(
        rules=RuleConfig(max_new_files_per_task=3),
        extension_points=[
            ExtensionPoint(
                name="Exporters",
                keywords=["export", "csv"],
                prefer_existing_paths=["src/**/exporters/**"],
                allow_new_files_under=["src/**/exporters/**", "tests/**"],
            )
        ],
    )
    task = TaskConfig(
        goal="Add CSV export support",
        prefer_modify=["src/demo/exporters/base.py"],
        expected_change_type="modify-only",
    )

    result = check_module_sprawl(
        [ChangedFile("src/demo/exporters/csv.py", "A")],
        config,
        task,
    )

    assert result.status == "WARN"
