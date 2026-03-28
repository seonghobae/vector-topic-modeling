from __future__ import annotations

from pathlib import Path
import re

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
    assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true" in workflow
    assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: false" not in workflow
    assert "name: Wait for dependency snapshot propagation" in workflow
    assert "run: sleep 15" in workflow

    for relpath in [
        "ARCHITECTURE.md",
        "docs/engineering/acceptance-criteria.md",
        "docs/security/api-security-checklist.md",
    ]:
        content = _read(relpath)
        assert "moderate-severity" in content, relpath
        assert "high-severity known vulnerabilities" not in content, relpath
        if relpath == "docs/security/api-security-checklist.md":
            assert "comment-summary-in-pr: on-failure" in content
            assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true" in content
            assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: false" not in content
            assert (
                "ahead of the Node 20 GitHub Actions deprecation window" not in content
            )
            assert "snapshot propagation" in content


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

    harness_doc = _read("docs/engineering/harness-engineering.md")
    assert "dependency_review_warning_gate.py" in harness_doc
    assert "pr_check_gate_classifier.py" in harness_doc


def test_ci_runs_docstring_coverage_step_once_for_python_311() -> None:
    workflow = _read(".github/workflows/ci.yml")

    assert "name: Report and verify docstring coverage" in workflow
    assert "if: matrix.python-version == '3.11'" in workflow
    assert workflow.count("name: Report and verify docstring coverage") == 1
    assert workflow.count("if: matrix.python-version == '3.11'") == 1


def test_dependency_review_runtime_monitor_workflow_and_docs_are_aligned() -> None:
    workflow = _read(".github/workflows/dependency-review-runtime-monitor.yml")

    assert "name: Dependency Review Runtime Monitor" in workflow
    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "scripts/review_checks/dependency_review_action_runtime_check.py" in workflow
    assert "actions/dependency-review-action@v4" in workflow
    assert (
        re.search(r"actions/dependency-review-action@[0-9a-f]{40}\b", workflow) is None
    )
    assert "--expected-runtime node24" in workflow
    assert "name: Fail on unexpected monitor exit code" in workflow
    assert "steps.runtime_check.outputs.exit_code != '0'" in workflow
    assert "steps.runtime_check.outputs.exit_code != '1'" in workflow
    assert "steps.runtime_check.outputs.exit_code != '2'" in workflow
    assert "- message:" in workflow
    assert 'payload.get("status") == "fetch-error"' in workflow
    assert "retry monitor via workflow_dispatch" in workflow
    assert "raw.githubusercontent.com availability" in workflow
    assert 'payload.get("status") in {"parse-error", "unexpected-error"}' in workflow
    assert "repair runtime monitor parser/logic" in workflow
    assert "fetch-error => retry + availability check" in workflow
    assert "parse-error/unexpected-error => repair monitor" in workflow

    for relpath in [
        "ARCHITECTURE.md",
        "docs/engineering/harness-engineering.md",
        "docs/security/api-security-checklist.md",
    ]:
        content = _read(relpath)
        assert "dependency-review-runtime-monitor.yml" in content, relpath

    security_doc = _read("docs/security/api-security-checklist.md")
    assert "Issue #45" in security_doc

    harness_doc = _read("docs/engineering/harness-engineering.md")
    assert "`fetch-error`: retry first" in harness_doc
    assert "`parse-error` or `unexpected-error`: repair-focused path" in harness_doc


def test_ci_stability_workflow_covers_python_313_and_314() -> None:
    workflow = _read(".github/workflows/ci-stability.yml")

    assert "name: ci-stability" in workflow
    assert "pull_request:" in workflow
    assert "branches: [main]" in workflow
    assert "push:" in workflow
    assert "schedule:" in workflow
    assert '- cron: "23 3 * * 2"' in workflow
    assert 'python-version: "3.13"' in workflow
    assert 'python-version: "3.14"' in workflow
    assert "continue-on-error: ${{ matrix.experimental }}" in workflow
    assert "name: stability (py${{ matrix.python-version }})" in workflow


def test_pr_branch_guard_workflow_enforces_dev_to_main_policy() -> None:
    workflow = _read(".github/workflows/pr-branch-guard.yml")

    assert "name: PR Branch Guard" in workflow
    assert "pull_request:" in workflow
    assert "branches: [main]" in workflow
    assert "override:branch-guard" in workflow
    assert re.search(r"actions/github-script@[0-9a-f]{40}", workflow) is not None
    assert "actions/github-script@v7" not in workflow
    assert 'const isDev = head === "dev";' in workflow
    assert "const isHotfix = /^hotfix" in workflow
    assert "const isRelease = /^release" in workflow
    assert "Blocked: PRs targeting 'main' must come from 'dev'" in workflow

    for relpath in [
        "ARCHITECTURE.md",
        "docs/operations/deploy-runbook.md",
        "docs/maintainers/releasing.md",
        "docs/workflow/pr-continuity.md",
    ]:
        content = _read(relpath)
        assert "Enforce head branch policy" in content, relpath
        assert "stability (py3.13)" in content, relpath
