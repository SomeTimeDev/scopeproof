from __future__ import annotations

from scopeproof.checks.public_api_growth import check_public_api_growth
from scopeproof.config import ProjectConfig, RuleConfig
from scopeproof.models import PASS, WARN, ChangedFile, Symbol


def test_public_api_growth_warns_when_limit_exceeded():
    config = ProjectConfig(rules=RuleConfig(max_new_public_symbols_per_task=1))
    symbols = [
        Symbol("CSVExporter", "class", "src/demo/exporters/csv.py", 1, True),
        Symbol("export_csv", "function", "src/demo/exporters/csv.py", 5, True),
    ]

    result = check_public_api_growth(
        [ChangedFile("src/demo/exporters/csv.py", "A")],
        symbols,
        [],
        config,
    )

    assert result.status == WARN


def test_public_api_growth_ignores_private_and_test_symbols():
    config = ProjectConfig(rules=RuleConfig(max_new_public_symbols_per_task=1))
    symbols = [
        Symbol("_private", "function", "src/demo/exporters/csv.py", 1, False),
        Symbol("test_export_csv", "function", "tests/test_csv.py", 1, True),
    ]

    result = check_public_api_growth(
        [
            ChangedFile("src/demo/exporters/csv.py", "A"),
            ChangedFile("tests/test_csv.py", "A"),
        ],
        symbols,
        [],
        config,
    )

    assert result.status == PASS

