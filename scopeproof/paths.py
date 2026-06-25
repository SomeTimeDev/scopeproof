from __future__ import annotations

from pathlib import Path

from pathspec import PathSpec


def normalize_path(path: str | Path) -> str:
    normalized = str(path).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def _spec(patterns: list[str]) -> PathSpec:
    return PathSpec.from_lines("gitwildmatch", patterns)


def matches_any(path: str, patterns: list[str]) -> bool:
    if not patterns:
        return False
    return _spec(patterns).match_file(normalize_path(path))


def filter_included(paths: list[str], include: list[str], exclude: list[str]) -> list[str]:
    included = _spec(include or ["**/*"])
    excluded = _spec(exclude)
    return [
        path
        for path in (normalize_path(item) for item in paths)
        if included.match_file(path) and not excluded.match_file(path)
    ]

