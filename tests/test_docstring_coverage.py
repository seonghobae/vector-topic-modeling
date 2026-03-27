from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "vector_topic_modeling"
DOCSTRING_COVERAGE_PATH = REPO_ROOT / "scripts" / "docstring_coverage.py"


def _load_docstring_coverage_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "docstring_coverage_test_target", DOCSTRING_COVERAGE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


docstring_coverage = _load_docstring_coverage_module()


def _iter_symbol_docstrings(file_path: Path) -> list[tuple[str, bool]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    rel = file_path.relative_to(REPO_ROOT)
    symbols: list[tuple[str, bool]] = [
        (f"{rel}:<module>", bool(ast.get_docstring(tree)))
    ]
    symbols.extend(
        (f"{rel}:{node.name}", bool(ast.get_docstring(node)))
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )
    return symbols


def test_product_code_docstring_coverage_is_full() -> None:
    missing: list[str] = []
    for file_path in sorted(SRC_ROOT.rglob("*.py")):
        for symbol_name, has_docstring in _iter_symbol_docstrings(file_path):
            if not has_docstring:
                missing.append(symbol_name)

    assert not missing, "Missing docstrings:\n" + "\n".join(missing)


def test_parse_args_accepts_threshold_and_paths(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "docstring_coverage.py",
            "--repo-root",
            str(REPO_ROOT),
            "--src-root",
            "src/vector_topic_modeling",
            "--min-percent",
            "99.5",
        ],
    )

    args = docstring_coverage.parse_args()

    assert args.repo_root == REPO_ROOT
    assert args.src_root == Path("src/vector_topic_modeling")
    assert args.min_percent == 99.5


def _patch_main_inputs(
    monkeypatch,
    *,
    report: Any,
    min_percent: float,
) -> None:
    monkeypatch.setattr(
        docstring_coverage,
        "parse_args",
        lambda: SimpleNamespace(
            repo_root=REPO_ROOT,
            src_root=Path("src/vector_topic_modeling"),
            min_percent=min_percent,
        ),
    )
    monkeypatch.setattr(
        docstring_coverage,
        "build_docstring_coverage_report",
        lambda *, repo_root, src_root: report,
    )


def test_main_returns_nonzero_when_no_symbols_discovered(monkeypatch, capsys) -> None:
    _patch_main_inputs(
        monkeypatch,
        report=docstring_coverage.DocstringCoverageReport(
            total_symbols=0,
            documented_symbols=0,
            missing_symbols=[],
        ),
        min_percent=100.0,
    )

    exit_code = docstring_coverage.main()

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "docstring_coverage total=0 documented=0" in output
    assert "No Python symbols were discovered" in output


def test_main_returns_nonzero_when_coverage_below_threshold(
    monkeypatch, capsys
) -> None:
    _patch_main_inputs(
        monkeypatch,
        report=docstring_coverage.DocstringCoverageReport(
            total_symbols=4,
            documented_symbols=3,
            missing_symbols=["src/vector_topic_modeling/mod.py:missing"],
        ),
        min_percent=100.0,
    )

    exit_code = docstring_coverage.main()

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "percent=75.00" in output
    assert "missing_symbols:" in output
    assert "src/vector_topic_modeling/mod.py:missing" in output


def test_main_returns_zero_when_threshold_is_met(monkeypatch, capsys) -> None:
    _patch_main_inputs(
        monkeypatch,
        report=docstring_coverage.DocstringCoverageReport(
            total_symbols=5,
            documented_symbols=5,
            missing_symbols=[],
        ),
        min_percent=100.0,
    )

    exit_code = docstring_coverage.main()

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "docstring_coverage total=5 documented=5 percent=100.00" in output
