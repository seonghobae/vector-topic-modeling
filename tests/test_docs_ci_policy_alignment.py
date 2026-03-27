from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relpath: str) -> str:
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def test_required_check_documents_include_dependency_review_gate() -> None:
    required_checks_phrase = "dependency-review"
    for relpath in [
        "ARCHITECTURE.md",
        "docs/maintainers/releasing.md",
        "docs/operations/deploy-runbook.md",
        "docs/workflow/pr-continuity.md",
    ]:
        assert required_checks_phrase in _read(relpath), relpath


def test_dependency_review_severity_wording_matches_workflow_setting() -> None:
    workflow = _read(".github/workflows/dependency-review.yml")
    assert "fail-on-severity: moderate" in workflow
    assert "retry-on-snapshot-warnings: true" in workflow
    assert "comment-summary-in-pr: on-failure" in workflow
    assert "comment-summary-in-pr: always" not in workflow

    for relpath in [
        "ARCHITECTURE.md",
        "docs/engineering/acceptance-criteria.md",
        "docs/security/api-security-checklist.md",
    ]:
        content = _read(relpath)
        assert "moderate-severity" in content, relpath
        assert "high-severity known vulnerabilities" not in content, relpath

    api_checklist = _read("docs/security/api-security-checklist.md")
    assert "comment-summary-in-pr: on-failure" in api_checklist


def test_dependency_submission_workflow_tracks_uv_lock_snapshots() -> None:
    workflow = _read(".github/workflows/dependency-submission.yml")

    assert "component-detection-dependency-submission-action" in workflow
    assert (
        "detectorArgs: Pip=EnableIfDefaultOff,SimplePip=EnableIfDefaultOff,UvLock=EnableIfDefaultOff"
        in workflow
    )
    assert (
        "if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.fork == false"
        in workflow
    )
