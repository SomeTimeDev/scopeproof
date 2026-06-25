from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from scopeproof.errors import ConfigError

DEFAULT_EXCLUDE = [
    ".git/**",
    ".venv/**",
    "venv/**",
    "node_modules/**",
    "dist/**",
    "build/**",
    "__pycache__/**",
    ".pytest_cache/**",
]


@dataclass(frozen=True)
class ProjectInfo:
    name: str | None = None
    mission: str | None = None
    non_goals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PathConfig:
    include: list[str] = field(default_factory=lambda: ["**/*"])
    exclude: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))


@dataclass(frozen=True)
class RuleConfig:
    max_changed_files_per_task: int = 12
    max_new_files_per_task: int = 3
    max_new_public_symbols_per_task: int = 6
    duplicate_symbol_similarity: float = 0.82
    fail_on_scope_escape: bool = True
    fail_on_module_sprawl: bool = False
    fail_on_duplicate_symbol: bool = False
    fail_on_orphan_new_file: bool = False
    fail_on_public_api_growth: bool = False
    fail_on_changed_file_growth: bool = False
    require_adr_for_new_module: bool = False
    adr_paths: list[str] = field(default_factory=lambda: ["docs/adr/*.md", "docs/architecture/*.md"])


@dataclass(frozen=True)
class ExtensionPoint:
    name: str
    keywords: list[str] = field(default_factory=list)
    prefer_existing_paths: list[str] = field(default_factory=list)
    allow_new_files_under: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ForbiddenImport:
    from_path: str
    to: str
    reason: str | None = None


@dataclass(frozen=True)
class ArchitectureConfig:
    forbidden_imports: list[ForbiddenImport] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectConfig:
    version: int = 1
    project: ProjectInfo = field(default_factory=ProjectInfo)
    paths: PathConfig = field(default_factory=PathConfig)
    rules: RuleConfig = field(default_factory=RuleConfig)
    extension_points: list[ExtensionPoint] = field(default_factory=list)
    architecture: ArchitectureConfig = field(default_factory=ArchitectureConfig)


@dataclass(frozen=True)
class TaskConfig:
    goal: str = ""
    allowed_paths: list[str] = field(default_factory=list)
    prefer_modify: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    expected_change_type: str | None = None
    expected_behavior: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}", suggestion=str(exc)) from exc
    except OSError as exc:
        raise ConfigError(f"Could not read {path}", suggestion=str(exc)) from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a YAML mapping.")
    return loaded


def _list(data: dict[str, Any], key: str, default: list[str] | None = None) -> list[str]:
    value = data.get(key, default or [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"Expected '{key}' to be a list of strings.")
    return list(value)


def load_project_config(path: Path) -> ProjectConfig:
    if not path.exists():
        raise ConfigError(
            f"Config file not found: {path}",
            suggestion="Run 'scopeproof init' or pass --config PATH.",
        )
    data = _load_yaml(path)
    version = data.get("version", 1)
    if not isinstance(version, int):
        raise ConfigError("'version' must be an integer.")

    project_data = data.get("project") or {}
    paths_data = data.get("paths") or {}
    rules_data = data.get("rules") or {}
    architecture_data = data.get("architecture") or {}

    project = ProjectInfo(
        name=project_data.get("name"),
        mission=project_data.get("mission"),
        non_goals=_list(project_data, "non_goals"),
    )
    paths = PathConfig(
        include=_list(paths_data, "include", ["**/*"]),
        exclude=_list(paths_data, "exclude", DEFAULT_EXCLUDE),
    )
    default_rules = RuleConfig()
    rules = RuleConfig(
        max_changed_files_per_task=int(
            rules_data.get("max_changed_files_per_task", default_rules.max_changed_files_per_task)
        ),
        max_new_files_per_task=int(
            rules_data.get("max_new_files_per_task", default_rules.max_new_files_per_task)
        ),
        max_new_public_symbols_per_task=int(
            rules_data.get(
                "max_new_public_symbols_per_task",
                default_rules.max_new_public_symbols_per_task,
            )
        ),
        duplicate_symbol_similarity=float(
            rules_data.get("duplicate_symbol_similarity", default_rules.duplicate_symbol_similarity)
        ),
        fail_on_scope_escape=bool(
            rules_data.get("fail_on_scope_escape", default_rules.fail_on_scope_escape)
        ),
        fail_on_module_sprawl=bool(
            rules_data.get("fail_on_module_sprawl", default_rules.fail_on_module_sprawl)
        ),
        fail_on_duplicate_symbol=bool(
            rules_data.get("fail_on_duplicate_symbol", default_rules.fail_on_duplicate_symbol)
        ),
        fail_on_orphan_new_file=bool(
            rules_data.get("fail_on_orphan_new_file", default_rules.fail_on_orphan_new_file)
        ),
        fail_on_public_api_growth=bool(
            rules_data.get("fail_on_public_api_growth", default_rules.fail_on_public_api_growth)
        ),
        fail_on_changed_file_growth=bool(
            rules_data.get(
                "fail_on_changed_file_growth",
                default_rules.fail_on_changed_file_growth,
            )
        ),
        require_adr_for_new_module=bool(
            rules_data.get("require_adr_for_new_module", default_rules.require_adr_for_new_module)
        ),
        adr_paths=_list(rules_data, "adr_paths", default_rules.adr_paths),
    )

    extension_points = []
    for item in data.get("extension_points") or []:
        if not isinstance(item, dict) or "name" not in item:
            raise ConfigError("Each extension point must be a mapping with a name.")
        extension_points.append(
            ExtensionPoint(
                name=str(item["name"]),
                keywords=_list(item, "keywords"),
                prefer_existing_paths=_list(item, "prefer_existing_paths"),
                allow_new_files_under=_list(item, "allow_new_files_under"),
                notes=_list(item, "notes"),
            )
        )

    forbidden_imports = []
    for item in architecture_data.get("forbidden_imports") or []:
        if not isinstance(item, dict):
            raise ConfigError("Each forbidden import rule must be a mapping.")
        forbidden_imports.append(
            ForbiddenImport(
                from_path=str(item.get("from", "")),
                to=str(item.get("to", "")),
                reason=item.get("reason"),
            )
        )

    return ProjectConfig(
        version=version,
        project=project,
        paths=paths,
        rules=rules,
        extension_points=extension_points,
        architecture=ArchitectureConfig(forbidden_imports=forbidden_imports),
    )


def default_project_config() -> ProjectConfig:
    return ProjectConfig()


def load_task_config(path: Path, goal_override: str | None = None) -> TaskConfig:
    if not path.exists():
        return TaskConfig(goal=goal_override or "")
    data = _load_yaml(path)
    goal = goal_override if goal_override is not None else str(data.get("goal") or "")
    return TaskConfig(
        goal=goal,
        allowed_paths=_list(data, "allowed_paths"),
        prefer_modify=_list(data, "prefer_modify"),
        forbidden_paths=_list(data, "forbidden_paths"),
        expected_change_type=data.get("expected_change_type"),
        expected_behavior=_list(data, "expected_behavior"),
        verification=_list(data, "verification"),
    )
