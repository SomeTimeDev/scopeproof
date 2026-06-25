from __future__ import annotations

from scopeproof.checks.duplicate_symbol import check_duplicate_symbol
from scopeproof.config import ProjectConfig
from scopeproof.models import PASS, WARN, ChangedFile, Symbol


def test_duplicate_symbol_flags_similar_public_class():
    current = [
        Symbol("CSVExporter", "class", "src/demo/exporters/csv.py", 1, True),
        Symbol("CSVExportService", "class", "src/demo/services/csv_export_service.py", 1, True),
    ]

    result = check_duplicate_symbol(
        [ChangedFile("src/demo/services/csv_export_service.py", "A")],
        current,
        [],
        ProjectConfig(),
    )

    assert result.status == WARN
    assert result.issues[0].path == "src/demo/services/csv_export_service.py"


def test_duplicate_symbol_ignores_private_and_unrelated_symbols():
    current = [
        Symbol("CSVExporter", "class", "src/demo/exporters/csv.py", 1, True),
        Symbol("_CSVExportService", "class", "src/demo/services/csv_export_service.py", 1, False),
        Symbol("PaymentLedger", "class", "src/demo/payments.py", 1, True),
    ]

    result = check_duplicate_symbol(
        [ChangedFile("src/demo/services/csv_export_service.py", "A")],
        current,
        [],
        ProjectConfig(),
    )

    assert result.status == PASS

