from __future__ import annotations

from scopeproof.checks.base import new_public_symbols, result_from_issues
from scopeproof.config import ProjectConfig
from scopeproof.indexer.symbols import (
    compatible_kinds,
    normalize_symbol_name,
    symbol_similarity,
    token_overlap_ratio,
)
from scopeproof.models import ChangedFile, CheckIssue, Symbol


def _is_duplicate_candidate(new_symbol: Symbol, existing: Symbol, threshold: float) -> tuple[bool, float]:
    if not compatible_kinds(new_symbol, existing):
        return False, 0.0
    left = normalize_symbol_name(new_symbol.name)
    right = normalize_symbol_name(existing.name)
    similarity = symbol_similarity(new_symbol, existing)
    substring_match = (
        (left in right or right in left)
        and min(len(left), len(right)) >= 4
        and abs(len(left) - len(right)) <= 12
    )
    overlap_match = token_overlap_ratio(left, right) >= 0.75 and len(set(left.split())) >= 2
    return similarity >= threshold or substring_match or overlap_match, similarity


def check_duplicate_symbol(
    changed_files: list[ChangedFile],
    current_symbols: list[Symbol],
    base_symbols: list[Symbol],
    config: ProjectConfig,
) -> object:
    issues: list[CheckIssue] = []
    new_symbols = new_public_symbols(
        changed_files=changed_files,
        current_symbols=current_symbols,
        base_symbols=base_symbols,
    )
    new_keys = {(symbol.path, symbol.kind, symbol.name, symbol.parent) for symbol in new_symbols}
    existing_symbols = [
        symbol
        for symbol in current_symbols
        if symbol.is_public and (symbol.path, symbol.kind, symbol.name, symbol.parent) not in new_keys
    ]

    for new_symbol in new_symbols:
        best: tuple[Symbol, float] | None = None
        for existing in existing_symbols:
            is_candidate, similarity = _is_duplicate_candidate(
                new_symbol,
                existing,
                config.rules.duplicate_symbol_similarity,
            )
            if is_candidate and (best is None or similarity > best[1]):
                best = (existing, similarity)
        if best is None:
            continue
        existing, similarity = best
        issues.append(
            CheckIssue(
                severity="WARN",
                message=(
                    f"New {new_symbol.kind} {new_symbol.name} is similar to existing "
                    f"{existing.kind} {existing.name}."
                ),
                path=new_symbol.path,
                line=new_symbol.line,
                suggestion=(
                    f"Extend the existing {existing.name} {existing.kind} unless a separate "
                    "abstraction is intentionally required."
                ),
                evidence={
                    "similarity": round(similarity, 3),
                    "existing_path": existing.path,
                    "existing_line": existing.line,
                },
            )
        )

    return result_from_issues(
        check_id="duplicate_symbol",
        title="Duplicate symbol",
        pass_summary="No duplicate-looking public symbols detected.",
        issue_summary=f"{len(issues)} duplicate-looking symbol(s) detected.",
        issues=issues,
        fail_enabled=config.rules.fail_on_duplicate_symbol,
    )

