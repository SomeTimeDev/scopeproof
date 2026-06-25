from __future__ import annotations

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
    captured = {}

    def fake_run_git(args, cwd):
        captured["args"] = args
        captured["cwd"] = cwd

        class Completed:
            stdout = "M\tsrc/app.py\n"

        return Completed()

    monkeypatch.setattr("scopeproof.git._run_git", fake_run_git)

    changed = get_changed_files("HEAD", None, tmp_path)

    assert captured["args"] == ["diff", "--name-status", "--find-renames", "HEAD"]
    assert changed[0].path == "src/app.py"

