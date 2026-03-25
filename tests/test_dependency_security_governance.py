from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]

DISMISSED_AS_PATTERN = r"- Dismissed as:\s+`(tolerable_risk|won't_fix)`"
DISMISSED_ON_PATTERN = (
    r"- Dismissed on(?: \(UTC\))?:\s+\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
)
DISMISSED_COMMENT_PATTERN = r"- Dismissed comment:\s+\S"


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
    assert "before each tagged release cut" in content
    assert "add it under resolved entries" in content


def test_dependency_exception_register_tracks_current_dismissed_advisory() -> None:
    content = read("docs/security/dependency-vulnerability-exceptions.md")

    assert re.search(r"GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}", content)
    assert "## Required fields per entry" in content
    assert "## Exception lifecycle (required)" in content
    assert "## Resolved exception entries" in content
    assert "## Active exception entries" in content
    assert "Last reviewed:" in content
    assert "Owner:" in content
    active_section = re.search(
        r"(?ms)^##\s+Active exception entries\s*\n(.*?)(?=^##\s+|\Z)",
        content,
    )
    assert active_section, "Expected active exception entries section"

    block = re.search(
        r"(?ms)^###\s+GHSA-5239-wwwm-4pmq.*?(?=^###\s+|\Z)",
        active_section.group(1),
    )
    assert block, "Expected active entry block for GHSA-5239-wwwm-4pmq"

    entry = block.group(0)
    assert re.search(DISMISSED_AS_PATTERN, entry)
    assert re.search(DISMISSED_ON_PATTERN, entry)
    assert re.search(DISMISSED_COMMENT_PATTERN, entry)
    assert "re-evaluation triggers" in content


def test_release_guide_contains_dependency_exception_gate() -> None:
    content = read("docs/maintainers/releasing.md")

    assert "## Dependency-exception release gate" in content
    assert "Resolved exception entries" in content
    assert "stop release prep" in content
