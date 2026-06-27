from __future__ import annotations

import pytest

from scopeproof.errors import ScopeProofError
from scopeproof.git import get_changed_files, parse_name_status


def test_parse_name_status_entries():
    changed = parse_name_status(
        "A\tsrc/new.py\n"
        "M\tsrc/existing.py\n"
        "D\tsrc/old.py\n"
        "R100\tsrc/old_name.py\tsrc/new_name.py\n"
        "C100\tsrc/source.py\tsrc/copy.py\n"
    )

    assert [(item.status, item.path, item.old_path) for item in changed] == [
        ("A", "src/new.py", None),
        ("M", "src/existing.py", None),
        ("D", "src/old.py", None),
        ("R", "src/new_name.py", "src/old_name.py"),
        ("C", "src/copy.py", "src/source.py"),
    ]


def test_working_tree_diff_command_construction(monkeypatch, tmp_path):
    captured = []

    def fake_run_git(args, cwd):
        captured.append((args, cwd))

        class Completed:
            stdout = "" if args[:2] == ["ls-files", "--others"] else "M\tsrc/app.py\n"

        return Completed()

    monkeypatch.setattr("scopeproof.git._run_git", fake_run_git)

    changed = get_changed_files("HEAD", None, tmp_path)

    assert captured[0][0] == ["diff", "--name-status", "--find-renames", "HEAD"]
    assert captured[1][0] == ["ls-files", "--others", "--exclude-standard"]
    assert changed[0].path == "src/app.py"


def test_get_changed_files_includes_untracked_and_deduplicates(monkeypatch, tmp_path):
    def fake_run_git(args, cwd):
        class Completed:
            stdout = (
                "A\tsrc/new.py\n"
                if args[0] == "diff"
                else "src/new.py\nsrc/other.py\n"
            )

        return Completed()

    monkeypatch.setattr("scopeproof.git._run_git", fake_run_git)

    changed = get_changed_files("HEAD", None, tmp_path)

    assert [(item.status, item.path) for item in changed] == [
        ("A", "src/new.py"),
        ("A", "src/other.py"),
    ]


def test_staged_diff_command_excludes_untracked(monkeypatch, tmp_path):
    captured = []

    def fake_run_git(args, cwd):
        captured.append(args)

        class Completed:
            stdout = "A\tsrc/staged.py\n"

        return Completed()

    monkeypatch.setattr("scopeproof.git._run_git", fake_run_git)

    changed = get_changed_files("HEAD", None, tmp_path, staged=True)

    assert captured == [["diff", "--name-status", "--find-renames", "--cached", "HEAD"]]
    assert [(item.status, item.path) for item in changed] == [("A", "src/staged.py")]


def test_ref_to_ref_diff_excludes_untracked_by_default(monkeypatch, tmp_path):
    captured = []

    def fake_run_git(args, cwd):
        captured.append(args)

        class Completed:
            stdout = "M\tsrc/ref_change.py\n"

        return Completed()

    monkeypatch.setattr("scopeproof.git._run_git", fake_run_git)

    changed = get_changed_files("origin/main", "HEAD", tmp_path)

    assert captured == [["diff", "--name-status", "--find-renames", "origin/main...HEAD"]]
    assert [(item.status, item.path) for item in changed] == [("M", "src/ref_change.py")]


def test_staged_diff_rejects_head_ref(tmp_path):
    with pytest.raises(ScopeProofError):
        get_changed_files("origin/main", "HEAD", tmp_path, staged=True)
