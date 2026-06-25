from __future__ import annotations

from scopeproof.checks.scope_escape import check_scope_escape
from scopeproof.config import ProjectConfig, TaskConfig
from scopeproof.models import FAIL, PASS, ChangedFile


def test_scope_escape_fails_for_forbidden_path():
    result = check_scope_escape(
        [ChangedFile("src/demo/services/export_service.py", "A")],
        ProjectConfig(),
        TaskConfig(
            allowed_paths=["src/**/exporters/**"],
            forbidden_paths=["src/**/services/**"],
        ),
    )

    assert result.status == FAIL
    assert len(result.issues) == 2


def test_scope_escape_passes_when_allowed_paths_empty():
    result = check_scope_escape(
        [ChangedFile("src/demo/exporters/csv.py", "M")],
        ProjectConfig(),
        TaskConfig(),
    )

    assert result.status == PASS

