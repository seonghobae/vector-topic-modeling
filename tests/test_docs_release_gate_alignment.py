from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def required_release_gate_fragments() -> list[str]:
    return [
        "uv run pytest -q",
        "uv run python scripts/docstring_coverage.py --min-percent 100",
        "uv run python -m build",
        "uv run python scripts/smoke_installed_cli.py",
        "--dist-dir dist",
        "--venv-dir .venv-smoke-cli",
    ]


def test_acceptance_criteria_requires_cli_smoke_gate() -> None:
    content = read("docs/engineering/acceptance-criteria.md")

    assert "uv run pytest -q" in content
    assert "uv run python scripts/docstring_coverage.py --min-percent 100" in content
    assert "uv run python -m build" in content
    assert "uv run python scripts/smoke_installed_cli.py" in content
    assert "--dist-dir dist" in content
    assert "--venv-dir .venv-smoke-cli" in content


def test_harness_engineering_is_uv_first_and_no_legacy_python3_commands() -> None:
    content = read("docs/engineering/harness-engineering.md")

    assert "uv run pytest -q" in content
    assert "uv run python scripts/docstring_coverage.py --min-percent 100" in content
    assert "uv run python -m build" in content
    assert "uv run python scripts/smoke_installed_cli.py" in content
    assert "--dist-dir dist" in content
    assert "--venv-dir .venv-smoke-cli" in content
    assert "python3 -m pytest" not in content
    assert "python3 -m build" not in content


def test_release_gate_fragments_match_docs_and_workflows() -> None:
    docs = "\n".join(
        [
            read("docs/engineering/acceptance-criteria.md"),
            read("docs/engineering/harness-engineering.md"),
        ]
    )
    workflow_contents = {
        ".github/workflows/ci.yml": read(".github/workflows/ci.yml"),
        ".github/workflows/publish.yml": read(".github/workflows/publish.yml"),
        ".github/workflows/release.yml": read(".github/workflows/release.yml"),
    }

    for fragment in required_release_gate_fragments():
        assert fragment in docs
        for path, content in workflow_contents.items():
            assert fragment in content, f"missing fragment in {path}: {fragment}"


def test_gitignore_covers_local_automation_artifacts() -> None:
    content = read(".gitignore")

    assert ".mypy_cache/" in content
    assert ".ruff_cache/" in content
    assert "registered_agents.json" in content
    assert "task_agent_mapping.json" in content
