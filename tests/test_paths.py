from __future__ import annotations

from scopeproof.paths import filter_included, matches_any, normalize_path


def test_matches_src_glob():
    assert matches_any("src/demo/app.py", ["src/**"])


def test_excludes_venv_path():
    assert filter_included(["src/app.py", ".venv/lib/site.py"], ["**/*"], [".venv/**"]) == [
        "src/app.py"
    ]


def test_normalizes_windows_separators():
    assert normalize_path("src\\demo\\app.py") == "src/demo/app.py"

