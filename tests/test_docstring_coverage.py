from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "vector_topic_modeling"


def _iter_symbol_docstrings(file_path: Path) -> list[tuple[str, bool]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    symbols: list[tuple[str, bool]] = []
    symbols.append(
        (f"{file_path.relative_to(REPO_ROOT)}:<module>", bool(ast.get_docstring(tree)))
    )
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(
                (
                    f"{file_path.relative_to(REPO_ROOT)}:{node.name}",
                    bool(ast.get_docstring(node)),
                )
            )
    return symbols


def test_product_code_docstring_coverage_is_full() -> None:
    missing: list[str] = []
    for file_path in sorted(SRC_ROOT.rglob("*.py")):
        for symbol_name, has_docstring in _iter_symbol_docstrings(file_path):
            if not has_docstring:
                missing.append(symbol_name)

    assert not missing, "Missing docstrings:\n" + "\n".join(missing)
