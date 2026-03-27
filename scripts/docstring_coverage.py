"""Measure AST-level docstring coverage for product Python modules."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocstringCoverageReport:
    """Aggregated docstring coverage metrics and missing-symbol list."""

    total_symbols: int
    documented_symbols: int
    missing_symbols: list[str]

    @property
    def percent(self) -> float:
        """Return documented-symbol percentage in the 0-100 range."""
        if self.total_symbols <= 0:
            return 100.0
        return (self.documented_symbols / self.total_symbols) * 100.0


def _iter_symbol_docstrings(repo_root: Path, file_path: Path) -> list[tuple[str, bool]]:
    """Collect ``(symbol_name, has_docstring)`` pairs for one Python file."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    symbols: list[tuple[str, bool]] = []
    rel_path = file_path.relative_to(repo_root)
    symbols.append((f"{rel_path}:<module>", bool(ast.get_docstring(tree))))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append((f"{rel_path}:{node.name}", bool(ast.get_docstring(node))))
    return symbols


def build_docstring_coverage_report(
    *, repo_root: Path, src_root: Path
) -> DocstringCoverageReport:
    """Build a docstring coverage report for all Python files under ``src_root``."""
    total = 0
    documented = 0
    missing: list[str] = []

    for file_path in sorted(src_root.rglob("*.py")):
        for symbol_name, has_docstring in _iter_symbol_docstrings(repo_root, file_path):
            total += 1
            if has_docstring:
                documented += 1
            else:
                missing.append(symbol_name)

    return DocstringCoverageReport(
        total_symbols=total,
        documented_symbols=documented,
        missing_symbols=missing,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for docstring coverage checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root used for relative symbol paths.",
    )
    parser.add_argument(
        "--src-root",
        type=Path,
        default=Path("src/vector_topic_modeling"),
        help="Source package directory to scan.",
    )
    parser.add_argument(
        "--min-percent",
        type=float,
        default=100.0,
        help="Minimum required docstring coverage percentage.",
    )
    return parser.parse_args()


def main() -> int:
    """Run docstring coverage measurement and return process exit code."""
    args = parse_args()
    repo_root = args.repo_root.resolve()
    src_root = (repo_root / args.src_root).resolve()

    report = build_docstring_coverage_report(repo_root=repo_root, src_root=src_root)

    print(
        "docstring_coverage "
        f"total={report.total_symbols} "
        f"documented={report.documented_symbols} "
        f"percent={report.percent:.2f}"
    )
    if report.total_symbols <= 0:
        print("No Python symbols were discovered for docstring coverage.")
        return 1
    if report.missing_symbols:
        print("missing_symbols:")
        for symbol_name in report.missing_symbols:
            print(symbol_name)

    if report.percent < float(args.min_percent):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
