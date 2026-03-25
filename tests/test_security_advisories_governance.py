from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def test_security_md_references_private_reporting_workflow() -> None:
    content = read("SECURITY.md")

    assert "security/advisories/new" in content
    assert "docs/security/security-advisories-workflow.md" in content
    assert "Please do not open a public GitHub issue" in content


def test_security_advisories_workflow_contains_required_sections() -> None:
    content = read("docs/security/security-advisories-workflow.md")
    lower_content = content.lower()

    required_sections = (
        "# GitHub Security Advisories Workflow",
        "## Scope",
        "## Roles and ownership",
        "## Intake and private reporting",
        "## Triage and severity",
        "## Private fix workflow",
        "## Publishing workflow",
        "## Dependency advisory handling",
        "## Dry-run rehearsal log",
    )

    positions: list[int] = []
    for fragment in required_sections:
        assert fragment in content
        positions.append(content.find(fragment))

    assert positions == sorted(positions)

    assert "Security > Advisories" in content
    assert "docs/security/dependency-vulnerability-exceptions.md" in content
    assert "Elapsed time" in content
    assert "Follow-up improvements" in content
    assert "affected versions" in content
    assert "first fixed version" in content

    sequence = [
        "fixed artifacts",
        "publish the github security advisory",
        "changelog.md",
    ]
    sequence_positions = [lower_content.find(token) for token in sequence]
    assert all(position != -1 for position in sequence_positions)
    assert sequence_positions == sorted(sequence_positions)


def test_security_workflow_requires_changelog_security_fix_entry() -> None:
    content = read("docs/security/security-advisories-workflow.md")

    assert "CHANGELOG.md" in content
    assert "security-fix summary" in content


def test_release_and_deploy_docs_include_security_advisory_gate() -> None:
    releasing = read("docs/maintainers/releasing.md")
    runbook = read("docs/operations/deploy-runbook.md")
    releasing_lower = releasing.lower()

    assert "## Security advisory release gate" in releasing
    assert "Before tagging:" in releasing
    assert "## Post-release security advisory publication" in releasing
    assert "After release publication:" in releasing
    assert "Security > Advisories" in releasing
    assert "publish the advisory" in releasing_lower
    assert "CHANGELOG.md" in releasing
    assert "advisory ID" in releasing
    assert "## Security advisory release coordination" in runbook
    assert "publish the GitHub Security Advisory" in runbook


def test_architecture_agents_and_acceptance_reference_workflow() -> None:
    architecture = read("ARCHITECTURE.md")
    agents_root = read("AGENTS.md")
    agents = read("docs/agents/README.md")
    acceptance = read("docs/engineering/acceptance-criteria.md")

    assert "docs/security/security-advisories-workflow.md" in architecture
    assert "GitHub Security Advisories" in architecture
    assert "docs/security/security-advisories-workflow.md" in agents_root
    assert "GitHub Security Advisories" in agents_root
    assert "docs/security/security-advisories-workflow.md" in agents
    assert "docs/security/security-advisories-workflow.md" in acceptance
