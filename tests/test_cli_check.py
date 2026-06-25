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
    statuses = {item["check_id"]: item["status"] for item in payload["results"]}
    assert statuses["scope_escape"] == "FAIL"
    assert statuses["module_sprawl"] == "FAIL"
    assert statuses["orphan_new_file"] == "WARN"


def test_cli_prompt_outputs_markdown(tmp_path, monkeypatch):
    write(tmp_path, "scopeproof.yml", demo_scopeproof_config())
    write(tmp_path, ".scopeproof/task.yml", demo_task_config())
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["prompt"])

    assert result.exit_code == 0
    assert "# Task" in result.stdout
    assert "Add CSV export support" in result.stdout
