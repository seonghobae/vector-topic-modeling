from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, NoReturn

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT / "scripts" / "review_checks" / "dependency_review_warning_gate.py"
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "dependency_review_warning_gate", SCRIPT_PATH
    )
    if spec is None:
        raise RuntimeError(f"Failed to create import spec for: {SCRIPT_PATH}")
    if spec.loader is None:
        raise RuntimeError(f"Missing loader for import spec: {SCRIPT_PATH}")
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


def test_parse_dependency_review_comment_without_warnings_is_clean() -> None:
    body = "Dependency review completed with no warning sections."

    summary = MODULE.parse_dependency_review_comment(body)

    assert summary.has_snapshot_warning is False
    assert summary.unknown_license_count == 0


def test_parse_dependency_review_comment_handles_plain_warning_emoji_variant() -> None:
    body = "⚠ 3 package(s) with unknown licenses."

    summary = MODULE.parse_dependency_review_comment(body)

    assert summary.unknown_license_count == 3


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


def test_evaluate_warning_policy_passes_when_within_limits() -> None:
    summary = MODULE.DependencyReviewWarningSummary(
        has_snapshot_warning=False,
        unknown_license_count=1,
    )

    ok, reasons = MODULE.evaluate_warning_policy(
        summary=summary,
        max_unknown_licenses=1,
        allow_snapshot_warning=True,
    )

    assert ok is True
    assert reasons == []


def test_evaluate_warning_policy_clamps_negative_max_unknown_licenses_to_zero() -> None:
    summary = MODULE.DependencyReviewWarningSummary(
        has_snapshot_warning=False,
        unknown_license_count=0,
    )

    ok, reasons = MODULE.evaluate_warning_policy(
        summary=summary,
        max_unknown_licenses=-5,
        allow_snapshot_warning=True,
    )

    assert ok is True
    assert reasons == []


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


def test_find_latest_dependency_review_comment_body_returns_none_without_marker() -> (
    None
):
    comments = [
        {
            "created_at": "2026-03-27T00:00:00Z",
            "user": {"login": "github-actions[bot]"},
            "body": "no marker present",
        }
    ]

    assert MODULE.find_latest_dependency_review_comment_body(comments) is None


def test_decode_comment_entry_handles_double_encoded_json_line() -> None:
    line = (
        '"{\\"user\\": {\\"login\\": \\"github-actions[bot]\\"}, \\"body\\": \\"x\\"}"'
    )

    decoded = MODULE._decode_comment_entry(line)

    assert decoded is not None
    assert decoded["user"]["login"] == "github-actions[bot]"


def test_run_gh_wraps_called_process_error() -> None:
    command = ["gh", "api", "/repos/example/example/issues/1/comments"]
    exc = subprocess.CalledProcessError(
        returncode=1,
        cmd=command,
        output="out",
        stderr="boom",
    )

    def _raise(*args: Any, **kwargs: Any) -> NoReturn:
        _ = args, kwargs
        raise exc

    original_run = MODULE.subprocess.run
    MODULE.subprocess.run = _raise
    try:
        try:
            MODULE._run_gh(command)
        except RuntimeError as err:
            message = str(err)
        else:
            raise AssertionError("expected RuntimeError")
    finally:
        MODULE.subprocess.run = original_run

    assert "gh command failed" in message
    assert "exit=1" in message


def test_main_returns_2_when_dependency_review_comment_is_missing(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            owner="seonghobae",
            repo="vector-topic-modeling",
            pr=41,
            max_unknown_licenses=0,
            allow_snapshot_warning=False,
        ),
    )
    monkeypatch.setattr(MODULE, "fetch_issue_comments", lambda **_: [])

    exit_code = MODULE.main()

    assert exit_code == 2
    output = capsys.readouterr().out
    assert '"status": "missing-comment"' in output


def test_main_returns_1_when_policy_evaluation_fails(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            owner="seonghobae",
            repo="vector-topic-modeling",
            pr=41,
            max_unknown_licenses=0,
            allow_snapshot_warning=False,
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_issue_comments",
        lambda **_: [
            {
                "created_at": "2026-03-27T00:00:00Z",
                "user": {"login": "github-actions[bot]"},
                "body": "⚠️: No snapshots were found for the head SHA.\n<!-- dependency-review-pr-comment-marker -->",
            }
        ],
    )

    exit_code = MODULE.main()

    assert exit_code == 1
    output = capsys.readouterr().out
    assert '"status": "failed"' in output
    assert "snapshot-warning" in output


def test_main_returns_0_when_policy_passes(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            owner="seonghobae",
            repo="vector-topic-modeling",
            pr=41,
            max_unknown_licenses=1,
            allow_snapshot_warning=True,
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_issue_comments",
        lambda **_: [
            {
                "created_at": "2026-03-27T00:00:00Z",
                "user": {"login": "github-actions[bot]"},
                "body": "⚠️ 1 package(s) with unknown licenses.\n<!-- dependency-review-pr-comment-marker -->",
            }
        ],
    )

    exit_code = MODULE.main()

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"status": "ok"' in output


def test_main_returns_2_when_fetch_raises_runtime_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            owner="seonghobae",
            repo="vector-topic-modeling",
            pr=41,
            max_unknown_licenses=0,
            allow_snapshot_warning=False,
        ),
    )

    def _raise_error(**_: object) -> list[dict[str, object]]:
        raise RuntimeError("gh command failed")

    monkeypatch.setattr(MODULE, "fetch_issue_comments", _raise_error)

    exit_code = MODULE.main()

    assert exit_code == 2
    assert '"status": "gh-error"' in capsys.readouterr().out
