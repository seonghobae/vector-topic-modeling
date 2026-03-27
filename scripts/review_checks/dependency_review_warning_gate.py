#!/usr/bin/env python3
"""Evaluate dependency-review warning signals on a pull request."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import re
import subprocess
from typing import Any

DEPENDENCY_REVIEW_MARKER = "dependency-review-pr-comment-marker"
SNAPSHOT_WARNING_PATTERNS = (
    "No snapshots were found for the head SHA",
    "number of snapshots compared for the base SHA",
)
UNKNOWN_LICENSE_PATTERN = re.compile(
    r"⚠️\s*(\d+)\s*package\(s\)\s*with unknown licenses",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class DependencyReviewWarningSummary:
    """Structured warning summary parsed from dependency-review comments."""

    has_snapshot_warning: bool
    unknown_license_count: int


def parse_dependency_review_comment(body: str) -> DependencyReviewWarningSummary:
    """Extract snapshot and unknown-license warning signals from comment text."""
    normalized = body.replace("\\n", "\n")
    has_snapshot_warning = any(
        token.lower() in normalized.lower() for token in SNAPSHOT_WARNING_PATTERNS
    )
    unknown_license_match = UNKNOWN_LICENSE_PATTERN.search(normalized)
    unknown_license_count = (
        int(unknown_license_match.group(1)) if unknown_license_match else 0
    )
    return DependencyReviewWarningSummary(
        has_snapshot_warning=has_snapshot_warning,
        unknown_license_count=unknown_license_count,
    )


def evaluate_warning_policy(
    *,
    summary: DependencyReviewWarningSummary,
    max_unknown_licenses: int,
    allow_snapshot_warning: bool,
) -> tuple[bool, list[str]]:
    """Validate parsed warning summary against configured acceptance limits."""
    reasons: list[str] = []
    if summary.has_snapshot_warning and not allow_snapshot_warning:
        reasons.append("snapshot-warning")
    if summary.unknown_license_count > max_unknown_licenses:
        reasons.append(
            f"unknown-licenses:{summary.unknown_license_count}>{max_unknown_licenses}"
        )
    return not reasons, reasons


def _decode_comment_entry(line: str) -> dict[str, Any] | None:
    """Decode one JSON-line comment entry from paginated gh output."""
    candidate = line.strip()
    if not candidate:
        return None
    item = json.loads(candidate)
    if isinstance(item, str):
        item = json.loads(item)
    if isinstance(item, dict):
        return item
    return None


def _run_gh(command: list[str]) -> str:
    """Execute gh command and return captured stdout text."""
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout


def fetch_issue_comments(
    *, owner: str, repo: str, pull_number: int
) -> list[dict[str, Any]]:
    """Fetch all pull-request issue comments using paginated GitHub API calls."""
    output = _run_gh(
        [
            "gh",
            "api",
            "--paginate",
            "-q",
            ".[] | @json",
            f"/repos/{owner}/{repo}/issues/{pull_number}/comments",
        ]
    )
    comments: list[dict[str, Any]] = []
    for line in output.splitlines():
        decoded = _decode_comment_entry(line)
        if decoded is not None:
            comments.append(decoded)
    return comments


def find_latest_dependency_review_comment_body(
    comments: list[dict[str, Any]],
) -> str | None:
    """Return the newest dependency-review bot comment body if present."""
    ordered = sorted(comments, key=lambda c: str(c.get("created_at", "")), reverse=True)
    for comment in ordered:
        user = comment.get("user")
        login = str(user.get("login", "")).lower() if isinstance(user, dict) else ""
        if login != "github-actions[bot]":
            continue
        body = str(comment.get("body", ""))
        if DEPENDENCY_REVIEW_MARKER in body:
            return body
    return None


def parse_args() -> argparse.Namespace:
    """Build command-line arguments for dependency-review warning evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate dependency-review warning state for one pull request."
    )
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    parser.add_argument(
        "--max-unknown-licenses",
        type=int,
        default=0,
        help="Maximum allowed unknown-license count (default: 0)",
    )
    parser.add_argument(
        "--allow-snapshot-warning",
        action="store_true",
        help="Allow snapshot warning without failing gate",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint for dependency-review warning policy evaluation."""
    args = parse_args()
    comments = fetch_issue_comments(
        owner=args.owner, repo=args.repo, pull_number=args.pr
    )
    body = find_latest_dependency_review_comment_body(comments)
    if body is None:
        print(
            json.dumps(
                {
                    "status": "missing-comment",
                    "owner": args.owner,
                    "repo": args.repo,
                    "pr": args.pr,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    summary = parse_dependency_review_comment(body)
    ok, reasons = evaluate_warning_policy(
        summary=summary,
        max_unknown_licenses=max(int(args.max_unknown_licenses), 0),
        allow_snapshot_warning=bool(args.allow_snapshot_warning),
    )
    print(
        json.dumps(
            {
                "status": "ok" if ok else "failed",
                "summary": asdict(summary),
                "reasons": reasons,
                "owner": args.owner,
                "repo": args.repo,
                "pr": args.pr,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
