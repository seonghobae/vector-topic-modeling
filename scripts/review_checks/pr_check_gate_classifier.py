#!/usr/bin/env python3
"""Classify PR check contexts into required blockers vs optional warnings."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import sys

SUCCESS_STATES = {"success", "pass", "completed", "neutral", "skipped"}
FAILURE_STATES = {"failure", "fail", "error", "timed_out", "cancelled"}
PENDING_STATES = {"pending", "in_progress", "queued", "requested"}

MAIN_PR_REQUIRED_CHECKS = (
    "workflow-lint",
    "test-and-build (3.11)",
    "test-and-build (3.12)",
    "dependency-review",
    "stability (py3.13)",
    "Enforce head branch policy",
)

NON_MAIN_PR_REQUIRED_CHECKS = (
    "workflow-lint",
    "test-and-build (3.11)",
    "test-and-build (3.12)",
)


@dataclass(frozen=True)
class ParsedCheck:
    """One PR check/status context normalized for merge-gate evaluation."""

    name: str
    state: str
    completed_at: str | None


@dataclass(frozen=True)
class GateSummary:
    """Merge-gate classification of required and optional check states."""

    ok: bool
    required_blockers: list[str]
    required_pending: list[str]
    non_required_failures: list[str]
    non_required_pending: list[str]


def _normalize_state(raw: str) -> str:
    """Map raw check state/conclusion values to success/failure/pending."""
    state = str(raw or "").strip().lower()
    if state in SUCCESS_STATES:
        return "success"
    if state in FAILURE_STATES:
        return "failure"
    if state in PENDING_STATES:
        return "pending"
    return "pending"


def parse_pr_checks(payload: str) -> list[ParsedCheck]:
    """Parse JSON check payload and keep latest row per check context name."""
    raw_items = json.loads(payload)
    if not isinstance(raw_items, list):
        raise TypeError("payload must be a JSON list")

    latest_by_name: dict[str, ParsedCheck] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        state_source = str(item.get("state") or item.get("conclusion") or "")
        completed_at_raw = item.get("completedAt")
        completed_at = str(completed_at_raw) if completed_at_raw else None

        candidate = ParsedCheck(
            name=name,
            state=_normalize_state(state_source),
            completed_at=completed_at,
        )

        current = latest_by_name.get(name)
        if current is None:
            latest_by_name[name] = candidate
            continue
        current_completed = str(current.completed_at or "")
        candidate_completed = str(candidate.completed_at or "")
        if candidate_completed >= current_completed:
            latest_by_name[name] = candidate

    return sorted(latest_by_name.values(), key=lambda x: x.name)


def evaluate_checks(
    checks: list[ParsedCheck], required_contexts: set[str]
) -> GateSummary:
    """Evaluate required check contexts and separate optional failures."""
    required_sorted = sorted(ctx for ctx in required_contexts if ctx)
    by_name = {check.name: check for check in checks}

    required_blockers: list[str] = []
    required_pending: list[str] = []
    for context in required_sorted:
        check = by_name.get(context)
        if check is None:
            required_pending.append(context)
            continue
        if check.state == "failure":
            required_blockers.append(context)
        elif check.state != "success":
            required_pending.append(context)

    non_required_failures = sorted(
        check.name
        for check in checks
        if check.name not in required_contexts and check.state == "failure"
    )
    non_required_pending = sorted(
        check.name
        for check in checks
        if check.name not in required_contexts and check.state == "pending"
    )

    return GateSummary(
        ok=not required_blockers and not required_pending,
        required_blockers=required_blockers,
        required_pending=required_pending,
        non_required_failures=non_required_failures,
        non_required_pending=non_required_pending,
    )


def format_summary(summary: GateSummary) -> str:
    """Render a compact text summary for CI logs and issue evidence."""
    lines = [
        "gate="
        f"{'PASS' if summary.ok else 'FAIL'} "
        f"required_blockers={len(summary.required_blockers)} "
        f"required_pending={len(summary.required_pending)} "
        f"optional_failures={len(summary.non_required_failures)} "
        f"optional_pending={len(summary.non_required_pending)}"
    ]
    if summary.required_blockers:
        lines.append(f"required_blockers:[{', '.join(summary.required_blockers)}]")
    if summary.required_pending:
        lines.append(f"required_pending:[{', '.join(summary.required_pending)}]")
    if summary.non_required_failures:
        lines.append(f"optional_failures:[{', '.join(summary.non_required_failures)}]")
    if summary.non_required_pending:
        lines.append(f"optional_pending:[{', '.join(summary.non_required_pending)}]")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse CLI args for required check context configuration."""
    parser = argparse.ArgumentParser(
        description="Classify PR checks into required blockers vs optional statuses"
    )
    parser.add_argument(
        "--required-checks",
        default="",
        help="Comma-separated required check contexts",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help=(
            "Base branch used to choose required-check defaults when "
            "--required-checks is omitted"
        ),
    )
    return parser.parse_args()


def default_required_checks(base_branch: str) -> tuple[str, ...]:
    """Return default required-check contexts for the given PR base branch."""
    normalized = str(base_branch or "").strip().lower()
    if normalized == "main":
        return MAIN_PR_REQUIRED_CHECKS
    return NON_MAIN_PR_REQUIRED_CHECKS


def _read_stdin() -> str:
    """Read check payload JSON from stdin."""
    return sys.stdin.read()


def main() -> int:
    """CLI entrypoint: parse input JSON and print gate summary."""
    args = parse_args()
    required_checks_arg = str(args.required_checks).strip()
    if required_checks_arg:
        required_contexts = {
            context.strip()
            for context in required_checks_arg.split(",")
            if context.strip()
        }
    else:
        required_contexts = set(default_required_checks(str(args.base_branch)))

    payload = _read_stdin()
    try:
        checks = parse_pr_checks(payload)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"invalid-input: {exc}")
        return 2

    summary = evaluate_checks(checks, required_contexts)
    print(format_summary(summary))
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
