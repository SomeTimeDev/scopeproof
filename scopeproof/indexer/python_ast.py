from __future__ import annotations

import ast
from pathlib import Path

from scopeproof.indexer.symbols import is_public_name
from scopeproof.models import ImportEdge, Symbol
from scopeproof.paths import filter_included, normalize_path


def index_python_source(source: str, path: str) -> tuple[list[Symbol], list[ImportEdge]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], []

    normalized_path = normalize_path(path)
    symbols: list[Symbol] = []
    imports: list[ImportEdge] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="class",
                    path=normalized_path,
                    line=node.lineno,
                    is_public=is_public_name(node.name),
                )
            )
            for child in node.body:
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    symbols.append(
                        Symbol(
                            name=child.name,
                            kind="method",
                            path=normalized_path,
                            line=child.lineno,
                            is_public=is_public_name(child.name),
                            parent=node.name,
                        )
                    )
        elif isinstance(node, ast.FunctionDef):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="function",
                    path=normalized_path,
                    line=node.lineno,
                    is_public=is_public_name(node.name),
                )
            )
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(
                Symbol(
                    name=node.name,
                    kind="async_function",
                    path=normalized_path,
                    line=node.lineno,
                    is_public=is_public_name(node.name),
                )
            )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportEdge(
                        importer_path=normalized_path,
                        imported_module=alias.name,
                        imported_name=None,
                        line=node.lineno,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                imports.append(
                    ImportEdge(
                        importer_path=normalized_path,
                        imported_module=module,
                        imported_name=alias.name,
                        line=node.lineno,
                    )
                )

    return symbols, imports


def index_python_file(path: Path, repo_root: Path) -> tuple[list[Symbol], list[ImportEdge]]:
    rel_path = normalize_path(path.resolve().relative_to(repo_root.resolve()))
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [], []
    return index_python_source(source, rel_path)


def index_repo(
    repo_root: Path,
    include: list[str],
    exclude: list[str],
) -> tuple[list[Symbol], list[ImportEdge]]:
    python_paths = [
        normalize_path(path.relative_to(repo_root))
        for path in repo_root.rglob("*.py")
        if ".git" not in path.parts
    ]
    selected = filter_included(python_paths, include, exclude)
    symbols: list[Symbol] = []
    imports: list[ImportEdge] = []
    for rel_path in selected:
        file_symbols, file_imports = index_python_file(repo_root / rel_path, repo_root)
        symbols.extend(file_symbols)
        imports.extend(file_imports)
    return symbols, imports

