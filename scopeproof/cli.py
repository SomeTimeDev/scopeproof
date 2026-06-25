from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Annotated

import typer

from scopeproof.config import (
    default_project_config,
    load_project_config,
    load_task_config,
)
from scopeproof.errors import ConfigError, ScopeProofError
from scopeproof.git import get_repo_root
from scopeproof.indexer.python_ast import index_repo
from scopeproof.models import FAIL, WARN
from scopeproof.prompt.generate import generate_prompt
from scopeproof.report.console import render_console
from scopeproof.report.json_report import render_json
from scopeproof.report.markdown import render_markdown
from scopeproof.checks.runner import run_checks

app = typer.Typer(
    help="Check AI-agent-generated Git diffs for deterministic scope drift.",
    no_args_is_help=True,
)


def _template_text(name: str) -> str:
    return files("scopeproof.templates").joinpath(name).read_text(encoding="utf-8")


def _write_template(path: Path, template_name: str, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_template_text(template_name), encoding="utf-8")
    return True


def _exit_config_error(exc: ScopeProofError) -> None:
    typer.echo(f"Error: {exc.message}", err=True)
    if exc.command:
        typer.echo(f"Command: {' '.join(exc.command)}", err=True)
    if exc.stderr:
        typer.echo(exc.stderr, err=True)
    if exc.suggestion:
        typer.echo(f"Suggestion: {exc.suggestion}", err=True)
    raise typer.Exit(2)


def _load_config_or_default(path: Path):
    if path.exists():
        return load_project_config(path)
    return default_project_config()


@app.command("init")
def init_command(
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing generated files."),
    ] = False,
    with_agents: Annotated[
        bool,
        typer.Option("--with-agents", help="Also create AGENTS.md when missing."),
    ] = False,
) -> None:
    """Create starter ScopeProof config files."""
    root = Path.cwd()
    created = []
    skipped = []
    for target, template in [
        (root / "scopeproof.yml", "scopeproof.yml"),
        (root / ".scopeproof" / "task.yml", "task.yml"),
    ]:
        if _write_template(target, template, force):
            created.append(str(target.relative_to(root)))
        else:
            skipped.append(str(target.relative_to(root)))
    if with_agents:
        target = root / "AGENTS.md"
        if _write_template(target, "AGENTS.md", force):
            created.append(str(target.relative_to(root)))
        else:
            skipped.append(str(target.relative_to(root)))

    for path in created:
        typer.echo(f"Created {path}")
    for path in skipped:
        typer.echo(f"Skipped existing {path}")


@app.command("map")
def map_command(
    format_: Annotated[
        str,
        typer.Option("--format", help="Output format: console or json."),
    ] = "console",
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to scopeproof.yml."),
    ] = Path("scopeproof.yml"),
) -> None:
    """Print a quick Python symbol/import map."""
    try:
        repo_root = get_repo_root(Path.cwd())
        loaded_config = _load_config_or_default(repo_root / config)
        symbols, imports = index_repo(
            repo_root,
            loaded_config.paths.include,
            loaded_config.paths.exclude,
        )
    except (ScopeProofError, ConfigError) as exc:
        _exit_config_error(exc)

    if format_ == "json":
        import json
        from dataclasses import asdict

        typer.echo(
            json.dumps(
                {
                    "symbols": [asdict(symbol) for symbol in symbols],
                    "imports": [asdict(edge) for edge in imports],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if format_ != "console":
        _exit_config_error(ScopeProofError("Unsupported map format.", suggestion="Use console or json."))

    classes = [symbol for symbol in symbols if symbol.kind == "class"]
    functions = [symbol for symbol in symbols if symbol.kind in {"function", "async_function"}]
    lines = [
        "ScopeProof Project Map",
        "",
        f"Python files indexed: {len({symbol.path for symbol in symbols} | {edge.importer_path for edge in imports})}",
        f"Symbols: {len(symbols)}",
        f"Imports: {len(imports)}",
        "",
        "Top-level classes:",
    ]
    lines.extend(f"- {symbol.path}::{symbol.name}" for symbol in classes[:20])
    lines.extend(["", "Top-level functions:"])
    lines.extend(f"- {symbol.path}::{symbol.name}" for symbol in functions[:20])
    typer.echo("\n".join(lines))


@app.command("prompt")
def prompt_command(
    goal: Annotated[str | None, typer.Argument(help="Optional task goal.")] = None,
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to scopeproof.yml."),
    ] = Path("scopeproof.yml"),
    task: Annotated[
        Path,
        typer.Option("--task", help="Path to .scopeproof/task.yml."),
    ] = Path(".scopeproof/task.yml"),
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Optional output markdown file."),
    ] = None,
) -> None:
    """Generate a focused coding-agent prompt."""
    root = Path.cwd()
    try:
        loaded_config = _load_config_or_default(root / config)
        loaded_task = load_task_config(root / task, goal_override=goal)
    except (ScopeProofError, ConfigError) as exc:
        _exit_config_error(exc)
    rendered = generate_prompt(loaded_config, loaded_task, goal)
    if output:
        output.write_text(rendered, encoding="utf-8")
        typer.echo(f"Wrote {output}")
        return
    typer.echo(rendered)


@app.command("check")
def check_command(
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to scopeproof.yml."),
    ] = Path("scopeproof.yml"),
    task: Annotated[
        Path,
        typer.Option("--task", help="Path to .scopeproof/task.yml."),
    ] = Path(".scopeproof/task.yml"),
    base: Annotated[str, typer.Option("--base", help="Base Git ref.")] = "HEAD",
    head: Annotated[str | None, typer.Option("--head", help="Optional head Git ref.")] = None,
    goal: Annotated[str | None, typer.Option("--goal", help="Override task goal.")] = None,
    format_: Annotated[
        str,
        typer.Option("--format", help="Output format: console, json, or markdown."),
    ] = "console",
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Optional output file."),
    ] = None,
    fail_on_warn: Annotated[
        bool,
        typer.Option("--fail-on-warn", help="Exit 1 for WARN reports."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Show issue evidence."),
    ] = False,
) -> None:
    """Run all v0.1.0 scope checks."""
    try:
        repo_root = get_repo_root(Path.cwd())
        loaded_config = load_project_config(repo_root / config)
        loaded_task = load_task_config(repo_root / task, goal_override=goal)
        report = run_checks(repo_root, loaded_config, loaded_task, base, head)
    except (ScopeProofError, ConfigError) as exc:
        _exit_config_error(exc)

    if format_ == "console":
        rendered = render_console(report, verbose=verbose)
    elif format_ == "json":
        rendered = render_json(report)
    elif format_ == "markdown":
        rendered = render_markdown(report, verbose=verbose)
    else:
        _exit_config_error(
            ScopeProofError("Unsupported report format.", suggestion="Use console, json, or markdown.")
        )

    if output:
        output.write_text(rendered, encoding="utf-8")
    else:
        typer.echo(rendered, nl=False)

    if report.overall_status == FAIL or (fail_on_warn and report.overall_status == WARN):
        raise typer.Exit(1)
    raise typer.Exit(0)

