from __future__ import annotations

import json

from typer.testing import CliRunner

from scopeproof.cli import app

from conftest import commit_all, demo_scopeproof_config, demo_task_config, init_repo, run_git, write

runner = CliRunner()


def test_cli_help_commands_work():
    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["init", "--help"]).exit_code == 0
    assert runner.invoke(app, ["check", "--help"]).exit_code == 0


def test_cli_init_creates_config_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "--with-agents"])

    assert result.exit_code == 0
    assert (tmp_path / "scopeproof.yml").exists()
    assert (tmp_path / ".scopeproof" / "task.yml").exists()
    assert (tmp_path / "AGENTS.md").exists()


def test_cli_init_strict_enables_strict_fail_rules(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "--strict"])

    assert result.exit_code == 0
    config = (tmp_path / "scopeproof.yml").read_text(encoding="utf-8")
    assert "fail_on_module_sprawl: true" in config
    assert "fail_on_duplicate_symbol: true" in config
    assert "fail_on_orphan_new_file: true" in config
    assert "fail_on_public_api_growth: true" in config
    assert "fail_on_changed_file_growth: true" in config


def test_cli_check_json_reports_core_sprawl_scenario(tmp_path, monkeypatch):
    init_repo(tmp_path)
    write(tmp_path, "scopeproof.yml", demo_scopeproof_config())
    write(tmp_path, ".scopeproof/task.yml", demo_task_config())
    write(
        tmp_path,
        "src/demo/exporters/csv.py",
        "class CSVExporter:\n    def export(self):\n        return ''\n",
    )
    write(tmp_path, "src/demo/exporters/base.py", "class BaseExporter:\n    pass\n")
    write(tmp_path, "tests/test_exporters.py", "from demo.exporters.csv import CSVExporter\n")
    commit_all(tmp_path)
    write(
        tmp_path,
        "src/demo/services/csv_export_service.py",
        "class CSVExportService:\n    def export(self):\n        return ''\n",
    )
    run_git(tmp_path, "add", ".")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["overall_status"] == "FAIL"
    result_ids = [item["check_id"] for item in payload["results"]]
    assert "changed_file_growth" in result_ids
    assert "parse_error" in result_ids
    assert result_ids.index("parse_error") < result_ids.index("duplicate_symbol")
    statuses = {item["check_id"]: item["status"] for item in payload["results"]}
    assert statuses["scope_escape"] == "FAIL"
    assert statuses["module_sprawl"] == "FAIL"
    assert statuses["orphan_new_file"] == "WARN"


def test_cli_check_detects_untracked_new_python_module(tmp_path, monkeypatch):
    init_repo(tmp_path)
    write(tmp_path, "scopeproof.yml", demo_scopeproof_config())
    write(tmp_path, ".scopeproof/task.yml", demo_task_config())
    write(tmp_path, "src/demo/exporters/base.py", "class BaseExporter:\n    pass\n")
    commit_all(tmp_path)
    write(
        tmp_path,
        "src/demo/services/untracked_export_service.py",
        "class UntrackedExportService:\n    pass\n",
    )
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["check", "--format", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert {
        "path": "src/demo/services/untracked_export_service.py",
        "status": "A",
        "old_path": None,
    } in payload["changed_files"]
    statuses = {item["check_id"]: item["status"] for item in payload["results"]}
    assert statuses["scope_escape"] == "FAIL"


def test_cli_prompt_outputs_markdown(tmp_path, monkeypatch):
    write(tmp_path, "scopeproof.yml", demo_scopeproof_config())
    write(tmp_path, ".scopeproof/task.yml", demo_task_config())
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["prompt"])

    assert result.exit_code == 0
    assert "# Task" in result.stdout
    assert "Add CSV export support" in result.stdout
