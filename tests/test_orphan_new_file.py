from __future__ import annotations

from scopeproof.checks.orphan_new_file import check_orphan_new_file
from scopeproof.models import PASS, WARN, ChangedFile, ImportEdge, Symbol


def test_orphan_new_file_warns_when_unreferenced(tmp_path):
    result = check_orphan_new_file(
        [ChangedFile("src/demo/services/csv_export_service.py", "A")],
        [],
        [Symbol("CSVExportService", "class", "src/demo/services/csv_export_service.py", 1, True)],
        tmp_path,
        fail_enabled=False,
    )

    assert result.status == WARN


def test_orphan_new_file_passes_when_imported(tmp_path):
    result = check_orphan_new_file(
        [ChangedFile("src/demo/exporters/csv.py", "A")],
        [
            ImportEdge(
                importer_path="src/demo/cli.py",
                imported_module="demo.exporters.csv",
                imported_name="CSVExporter",
                line=1,
            )
        ],
        [Symbol("CSVExporter", "class", "src/demo/exporters/csv.py", 1, True)],
        tmp_path,
        fail_enabled=False,
    )

    assert result.status == PASS


def test_orphan_new_file_passes_for_test_and_init_files(tmp_path):
    result = check_orphan_new_file(
        [
            ChangedFile("tests/test_csv.py", "A"),
            ChangedFile("src/demo/exporters/__init__.py", "A"),
        ],
        [],
        [],
        tmp_path,
        fail_enabled=False,
    )

    assert result.status == PASS

