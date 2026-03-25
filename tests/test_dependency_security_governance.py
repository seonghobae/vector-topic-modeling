from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]


def read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def dependabot_update_blocks(content: str) -> dict[str, str]:
    blocks = re.findall(
        r"(?ms)^\s*-\s*package-ecosystem:\s*([^\n]+)\n(.*?)(?=^\s*-\s*package-ecosystem:|\Z)",
        content,
    )
    return {ecosystem.strip(): body for ecosystem, body in blocks}


def test_dependabot_config_covers_required_ecosystems() -> None:
    content = read(".github/dependabot.yml")
    update_blocks = dependabot_update_blocks(content)

    assert "version: 2" in content

    for ecosystem in ("pip", "github-actions"):
        assert ecosystem in update_blocks

        block = update_blocks[ecosystem]
        assert 'directory: "/"' in block
        assert "interval: weekly" in block
        assert "day: monday" in block
        assert 'time: "03:00"' in block
        assert "timezone: UTC" in block
        assert "open-pull-requests-limit:" in block


def test_api_security_checklist_includes_dependency_exception_policy() -> None:
    content = read("docs/security/api-security-checklist.md")

    assert "## Dependency supply-chain checks" in content
    assert ".github/dependabot.yml" in content
    assert "docs/security/dependency-vulnerability-exceptions.md" in content


def test_dependency_exception_register_tracks_current_dismissed_advisory() -> None:
    content = read("docs/security/dependency-vulnerability-exceptions.md")

    assert re.search(r"GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}", content)
    assert "## Required fields per entry" in content
    assert "## Active exception entries" in content
    assert "Last reviewed:" in content
    assert "Owner:" in content
    assert "tolerable_risk" in content
    assert "re-evaluation triggers" in content
