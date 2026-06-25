from __future__ import annotations

from scopeproof.checks.changed_file_growth import check_changed_file_growth
from scopeproof.config import ProjectConfig, RuleConfig
from scopeproof.models import FAIL, PASS, WARN, ChangedFile


def test_changed_file_growth_passes_within_limit():
    config = ProjectConfig(rules=RuleConfig(max_changed_files_per_task=2))

    result = check_changed_file_growth([ChangedFile("src/a.py", "M")], config)

    assert result.status == PASS


def test_changed_file_growth_warns_when_limit_exceeded():
    config = ProjectConfig(rules=RuleConfig(max_changed_files_per_task=1))

    result = check_changed_file_growth(
        [ChangedFile("src/a.py", "M"), ChangedFile("src/b.py", "M")],
        config,
    )

    assert result.status == WARN


def test_changed_file_growth_fails_when_configured():
    config = ProjectConfig(
        rules=RuleConfig(max_changed_files_per_task=1, fail_on_changed_file_growth=True)
    )

    result = check_changed_file_growth(
        [ChangedFile("src/a.py", "M"), ChangedFile("src/b.py", "M")],
        config,
    )

    assert result.status == FAIL

