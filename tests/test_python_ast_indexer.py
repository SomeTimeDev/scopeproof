from __future__ import annotations

from scopeproof.indexer.python_ast import index_python_source


def test_ast_indexer_extracts_symbols_and_imports():
    symbols, imports = index_python_source(
        """
import os
from pathlib import Path

class CSVExporter:
    def export(self):
        pass

def main():
    pass

async def amain():
    pass
""",
        "src/demo/exporters/csv.py",
    )

    assert ("CSVExporter", "class", None) in {
        (symbol.name, symbol.kind, symbol.parent) for symbol in symbols
    }
    assert ("export", "method", "CSVExporter") in {
        (symbol.name, symbol.kind, symbol.parent) for symbol in symbols
    }
    assert ("main", "function", None) in {
        (symbol.name, symbol.kind, symbol.parent) for symbol in symbols
    }
    assert ("amain", "async_function", None) in {
        (symbol.name, symbol.kind, symbol.parent) for symbol in symbols
    }
    assert ("os", None) in {(edge.imported_module, edge.imported_name) for edge in imports}
    assert ("pathlib", "Path") in {(edge.imported_module, edge.imported_name) for edge in imports}


def test_ast_indexer_handles_syntax_error_without_crashing():
    symbols, imports = index_python_source("def broken(:\n", "src/broken.py")

    assert symbols == []
    assert imports == []

