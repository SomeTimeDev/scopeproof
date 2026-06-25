from __future__ import annotations

import re
from difflib import SequenceMatcher

from scopeproof.models import Symbol

GENERIC_SUFFIXES = {
    "service",
    "manager",
    "helper",
    "util",
    "utils",
    "new",
    "v2",
    "impl",
    "implementation",
}


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def is_public_name(name: str) -> bool:
    return not name.startswith("_") and not is_dunder(name)


def normalize_symbol_name(name: str) -> str:
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
    spaced = re.sub(r"[_\-]+", " ", spaced)
    tokens = [token.lower() for token in spaced.split()]
    trimmed = [token for token in tokens if token not in GENERIC_SUFFIXES]
    return " ".join(trimmed or tokens)


def token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def symbol_similarity(left: Symbol, right: Symbol) -> float:
    left_name = normalize_symbol_name(left.name)
    right_name = normalize_symbol_name(right.name)
    return SequenceMatcher(None, left_name, right_name).ratio()


def compatible_kinds(left: Symbol, right: Symbol) -> bool:
    function_kinds = {"function", "async_function"}
    if left.kind == "class" or right.kind == "class":
        return left.kind == right.kind
    if left.kind in function_kinds and right.kind in function_kinds:
        return True
    if left.kind == "method" and right.kind == "method":
        if not left.parent or not right.parent:
            return False
        return SequenceMatcher(
            None,
            normalize_symbol_name(left.parent),
            normalize_symbol_name(right.parent),
        ).ratio() >= 0.75
    return False

