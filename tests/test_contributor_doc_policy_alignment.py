from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def _required_local_verification_fragments() -> list[str]:
    return [
        "uv run pytest -q",
        "uv run python scripts/docstring_coverage.py --min-percent 100",
        "rm -rf dist .venv-smoke-cli",
        "uv run python -m build",
        "uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli",
    ]


def _assert_fragments_in_order(
    content: str, fragments: list[str], *, relpath: str
) -> None:
    previous = -1
    for fragment in fragments:
        index = content.find(fragment, previous + 1)
        assert index >= 0, f"missing '{fragment}' in {relpath}"
        previous = index


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

    fragments = _required_local_verification_fragments()
    for relpath, content in docs.items():
        _assert_fragments_in_order(content, fragments, relpath=relpath)


def test_contributing_branching_guidance_matches_pr_branch_guard_policy() -> None:
    content = _read("CONTRIBUTING.md")

    assert "Create a branch from `dev`." in content
    assert "Create a branch from `main`." not in content
    assert "feature branches merge into `dev`" in content
    assert "`dev` merges into `main`" in content


def test_user_manual_documents_all_runtime_cli_tuning_options() -> None:
    content = _read("docs/user-manual.md")

    for option in [
        "--min-topics",
        "--max-topics",
        "--max-top-share",
        "--display-limit",
        "--use-session-representatives",
    ]:
        assert f"`{option}`" in content


def test_user_manual_documents_all_ingestion_config_keys() -> None:
    content = _read("docs/user-manual.md")

    for config_key in [
        "id_fields",
        "text_fields",
        "payload_fields",
        "content_fields",
        "question_fields",
        "response_fields",
        "session_id_fields",
        "session_key_fields",
        "count_field",
        "column_value_path",
        "column_name_field",
        "column_value_field",
        "max_text_chars",
    ]:
        assert f"`{config_key}`" in content


def test_user_manual_describes_text_resolution_fallback_order() -> None:
    content = _read("docs/user-manual.md")

    section_start = content.index("### 3.2 Input field behavior")
    section_end = content.index("### 3.3 Output shape")
    section = content[section_start:section_end]

    ordered_markers = [
        "`text_fields`",
        "`content_fields`",
        "`payload_fields`",
        "`question_fields`",
        "`response_fields`",
        "serialized row JSON",
    ]
    positions = [section.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)


def test_general_korean_manual_matches_python_api_contract() -> None:
    content = _read("docs/user-manual-general-ko.md")

    assert "OpenAICompatConfig(" in content
    assert "OpenAICompatEmbeddingProvider(" in content
    assert "topic.topic_id" in content
    assert "topic.total_count" in content
    assert "topic.texts[0]" in content

    assert "topic.id" not in content
    assert "topic.count" not in content
    assert "topic.display_texts" not in content


def test_general_korean_manual_uses_base_url_without_v1_suffix() -> None:
    content = _read("docs/user-manual-general-ko.md")

    base_url_values = re.findall(r'--base-url\s+"([^"]+)"', content)

    assert base_url_values, "docs/user-manual-general-ko.md missing --base-url examples"
    assert "https://api.openai.com" in base_url_values
    assert all(not url.rstrip("/").endswith("/v1") for url in base_url_values)
