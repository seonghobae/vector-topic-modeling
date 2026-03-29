from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def _required_local_verification_fragments() -> list[str]:
    return [
        "uv run pytest -q",
        "uv run python scripts/docstring_coverage.py --min-percent 100",
        "uv run python -m build",
        "uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli",
        "rm -rf dist .venv-smoke-cli",
    ]


def test_contributor_facing_docs_match_local_verification_contract() -> None:
    docs = {
        "README.md": _read("README.md"),
        "CONTRIBUTING.md": _read("CONTRIBUTING.md"),
        "AGENTS.md": _read("AGENTS.md"),
        "docs/user-manual.md": _read("docs/user-manual.md"),
        "docs/security/security-advisories-workflow.md": _read(
            "docs/security/security-advisories-workflow.md"
        ),
        ".github/PULL_REQUEST_TEMPLATE.md": _read(".github/PULL_REQUEST_TEMPLATE.md"),
    }

    for relpath, content in docs.items():
        for fragment in _required_local_verification_fragments():
            assert fragment in content, f"missing '{fragment}' in {relpath}"


def test_contributing_branching_guidance_matches_pr_branch_guard_policy() -> None:
    content = _read("CONTRIBUTING.md")

    assert "Create a branch from `dev`." in content
    assert "Create a branch from `main`." not in content
    assert "feature branches merge into `dev`" in content
    assert "`dev` merges into `main`" in content
