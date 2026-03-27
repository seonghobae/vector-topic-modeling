from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT / "scripts" / "review_checks" / "dependency_review_warning_gate.py"
)


def _load_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "dependency_review_warning_gate", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def test_parse_dependency_review_comment_detects_snapshot_warning_and_unknown_count() -> (
    None
):
    body = """<h2>Snapshot Warnings</h2>
⚠️: The number of snapshots compared for the base SHA (0) and the head SHA (1) do not match.
⚠️ 8 package(s) with unknown licenses.
<!-- dependency-review-pr-comment-marker -->
"""

    summary = MODULE.parse_dependency_review_comment(body)

    assert summary.has_snapshot_warning is True
    assert summary.unknown_license_count == 8


def test_parse_dependency_review_comment_detects_head_snapshot_missing_warning() -> (
    None
):
    body = """
    ⚠️: No snapshots were found for the head SHA.
    <!-- dependency-review-pr-comment-marker -->
    """

    summary = MODULE.parse_dependency_review_comment(body)

    assert summary.has_snapshot_warning is True
    assert summary.unknown_license_count == 0


def test_evaluate_warning_policy_fails_on_disallowed_snapshot_warning() -> None:
    summary = MODULE.DependencyReviewWarningSummary(
        has_snapshot_warning=True,
        unknown_license_count=0,
    )

    ok, reasons = MODULE.evaluate_warning_policy(
        summary=summary,
        max_unknown_licenses=0,
        allow_snapshot_warning=False,
    )

    assert ok is False
    assert "snapshot-warning" in reasons


def test_evaluate_warning_policy_fails_on_unknown_license_threshold() -> None:
    summary = MODULE.DependencyReviewWarningSummary(
        has_snapshot_warning=False,
        unknown_license_count=2,
    )

    ok, reasons = MODULE.evaluate_warning_policy(
        summary=summary,
        max_unknown_licenses=1,
        allow_snapshot_warning=True,
    )

    assert ok is False
    assert "unknown-licenses:2>1" in reasons


def test_find_latest_dependency_review_comment_body_ignores_other_comments() -> None:
    comments = [
        {"user": {"login": "other-bot"}, "body": "some comment"},
        {
            "user": {"login": "github-actions[bot]"},
            "body": "dependency review\n<!-- dependency-review-pr-comment-marker -->",
        },
    ]

    comment_body = MODULE.find_latest_dependency_review_comment_body(comments)

    assert comment_body is not None
    assert "dependency-review-pr-comment-marker" in comment_body
