from __future__ import annotations

from scopeproof.checks.parse_error import check_parse_error
from scopeproof.models import FAIL, PASS, ChangedFile


def test_parse_error_fails_for_invalid_changed_python_file(tmp_path):
    target = tmp_path / "src" / "broken.py"
    target.parent.mkdir(parents=True)
    target.write_text("def broken(:\n    pass\n", encoding="utf-8")

    result = check_parse_error([ChangedFile("src/broken.py", "M")], tmp_path)

    assert result.status == FAIL
    assert result.issues[0].path == "src/broken.py"
    assert result.issues[0].line == 1
    assert "Python syntax error" in result.issues[0].message


def test_parse_error_passes_for_valid_python_file(tmp_path):
    target = tmp_path / "src" / "ok.py"
    target.parent.mkdir(parents=True)
    target.write_text("def ok():\n    return True\n", encoding="utf-8")

    result = check_parse_error([ChangedFile("src/ok.py", "M")], tmp_path)

    assert result.status == PASS

