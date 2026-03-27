from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_project_license_is_spdx_expression_string() -> None:
    content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    project_block_match = re.search(r"(?ms)^\[project\]\n(.*?)(?=^\[|\Z)", content)
    assert project_block_match, "Expected [project] section in pyproject.toml"
    project_block = project_block_match.group(1)

    assert re.search(
        r'(?m)^\s*license\s*=\s*"[A-Za-z0-9 .()+\-]+"\s*$',
        project_block,
    ), (
        "Expected [project].license to be an SPDX expression string "
        '(e.g. "MIT" or "MIT OR Apache-2.0")'
    )

    assert not re.search(r"(?m)^\s*license\s*=\s*\{", project_block), (
        "Table-style [project].license (for example { text = ... }) "
        "is not SPDX-friendly"
    )

    assert re.search(
        r'(?m)^\s*license-files\s*=\s*\["LICENSE"\]\s*$', project_block
    ), "Expected [project].license-files to include LICENSE"


def test_security_checklist_mentions_spdx_project_license_policy() -> None:
    checklist = (REPO_ROOT / "docs/security/api-security-checklist.md").read_text(
        encoding="utf-8"
    )

    assert "[project].license" in checklist
    assert "SPDX expression string" in checklist
    assert 'license-files = ["LICENSE"]' in checklist
