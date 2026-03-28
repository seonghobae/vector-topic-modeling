from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import NoReturn

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "review_checks" / "pr_check_gate_classifier.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "pr_check_gate_classifier", SCRIPT_PATH
    )
    if spec is None:
        raise RuntimeError(f"Failed to create import spec for: {SCRIPT_PATH}")
    if spec.loader is None:
        raise RuntimeError(f"Missing loader for import spec: {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - defensive guard for loader failures
        sys.modules.pop(spec.name, None)
        raise RuntimeError(
            f"Failed to import module from {SCRIPT_PATH}: {exc}"
        ) from exc
    return module


MODULE = _load_module()


def test_parse_pr_checks_normalizes_state_values() -> None:
    payload = json.dumps(
        [
            {"name": "workflow-lint", "state": "SUCCESS"},
            {"name": "CodeRabbit", "state": "failure"},
            {"name": "dependency-review", "state": "in_progress"},
            {"name": "misc", "state": "unknown_state"},
        ]
    )

    checks = MODULE.parse_pr_checks(payload)

    by_name = {c.name: c for c in checks}
    assert by_name["workflow-lint"].state == "success"
    assert by_name["CodeRabbit"].state == "failure"
    assert by_name["dependency-review"].state == "pending"
    assert by_name["misc"].state == "pending"


def test_parse_pr_checks_keeps_latest_row_per_context() -> None:
    payload = json.dumps(
        [
            {
                "name": "dependency-review",
                "state": "FAILURE",
                "completedAt": "2026-03-27T00:00:00Z",
            },
            {
                "name": "dependency-review",
                "state": "SUCCESS",
                "completedAt": "2026-03-27T00:05:00Z",
            },
        ]
    )

    checks = MODULE.parse_pr_checks(payload)

    assert len(checks) == 1
    assert checks[0].name == "dependency-review"
    assert checks[0].state == "success"


def test_parse_pr_checks_raises_type_error_when_payload_decodes_to_non_list() -> None:
    payload = json.dumps({"name": "workflow-lint", "state": "success"})

    with pytest.raises(TypeError):
        MODULE.parse_pr_checks(payload)


def test_evaluate_checks_required_failure_is_blocker() -> None:
    checks = [
        MODULE.ParsedCheck(name="workflow-lint", state="failure", completed_at=None)
    ]

    summary = MODULE.evaluate_checks(checks, {"workflow-lint"})

    assert summary.ok is False
    assert summary.required_blockers == ["workflow-lint"]
    assert summary.required_pending == []


def test_evaluate_checks_required_pending_is_blocker() -> None:
    checks = [
        MODULE.ParsedCheck(name="dependency-review", state="pending", completed_at=None)
    ]

    summary = MODULE.evaluate_checks(checks, {"dependency-review"})

    assert summary.ok is False
    assert summary.required_blockers == []
    assert summary.required_pending == ["dependency-review"]


def test_evaluate_checks_missing_required_context_is_pending() -> None:
    checks = [
        MODULE.ParsedCheck(name="workflow-lint", state="success", completed_at=None)
    ]

    summary = MODULE.evaluate_checks(
        checks,
        {"workflow-lint", "test-and-build (3.12)"},
    )

    assert summary.ok is False
    assert summary.required_pending == ["test-and-build (3.12)"]


def test_evaluate_checks_non_required_failure_is_not_blocker() -> None:
    checks = [
        MODULE.ParsedCheck(name="workflow-lint", state="success", completed_at=None),
        MODULE.ParsedCheck(name="CodeRabbit", state="failure", completed_at=None),
    ]

    summary = MODULE.evaluate_checks(checks, {"workflow-lint"})

    assert summary.ok is True
    assert summary.required_blockers == []
    assert summary.required_pending == []
    assert summary.non_required_failures == ["CodeRabbit"]


def test_evaluate_checks_non_required_pending_is_not_blocker() -> None:
    checks = [
        MODULE.ParsedCheck(name="workflow-lint", state="success", completed_at=None),
        MODULE.ParsedCheck(
            name="code-quality-external",
            state="pending",
            completed_at=None,
        ),
    ]

    summary = MODULE.evaluate_checks(checks, {"workflow-lint"})

    assert summary.ok is True
    assert summary.non_required_pending == ["code-quality-external"]


def test_format_summary_pass_with_optional_failure() -> None:
    summary = MODULE.GateSummary(
        ok=True,
        required_blockers=[],
        required_pending=[],
        non_required_failures=["CodeRabbit"],
        non_required_pending=[],
    )

    text = MODULE.format_summary(summary)

    assert (
        text.splitlines()[0]
        == "gate=PASS required_blockers=0 required_pending=0 optional_failures=1 optional_pending=0"
    )
    assert "optional_failures:[CodeRabbit]" in text


def test_format_summary_fail_with_required_blocker() -> None:
    summary = MODULE.GateSummary(
        ok=False,
        required_blockers=["test-and-build (3.12)"],
        required_pending=["dependency-review"],
        non_required_failures=["CodeRabbit"],
        non_required_pending=[],
    )

    text = MODULE.format_summary(summary)

    assert (
        text.splitlines()[0]
        == "gate=FAIL required_blockers=1 required_pending=1 optional_failures=1 optional_pending=0"
    )
    assert "required_blockers:[test-and-build (3.12)]" in text
    assert "required_pending:[dependency-review]" in text
    assert "optional_failures:[CodeRabbit]" in text


def test_main_returns_0_when_required_contexts_are_green(monkeypatch, capsys) -> None:
    payload = json.dumps(
        [
            {"name": "workflow-lint", "state": "success"},
            {"name": "CodeRabbit", "state": "failure"},
        ]
    )
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(required_checks="workflow-lint"),
    )
    monkeypatch.setattr(MODULE, "_read_stdin", lambda: payload)

    exit_code = MODULE.main()

    assert exit_code == 0
    assert "gate=PASS" in capsys.readouterr().out


def test_parse_args_default_required_checks_match_main_branch_policy(
    monkeypatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["pr_check_gate_classifier"])

    args = MODULE.parse_args()
    parsed = {fragment.strip() for fragment in str(args.required_checks).split(",")}

    assert parsed == {
        "workflow-lint",
        "test-and-build (3.11)",
        "test-and-build (3.12)",
        "dependency-review",
        "stability (py3.13)",
        "Enforce head branch policy",
    }


def test_main_returns_1_when_required_context_fails(monkeypatch, capsys) -> None:
    payload = json.dumps(
        [
            {"name": "dependency-review", "state": "failure"},
        ]
    )
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(required_checks="dependency-review"),
    )
    monkeypatch.setattr(MODULE, "_read_stdin", lambda: payload)

    exit_code = MODULE.main()

    assert exit_code == 1
    assert "gate=FAIL" in capsys.readouterr().out


def test_main_returns_2_when_input_is_not_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(required_checks="workflow-lint"),
    )
    monkeypatch.setattr(MODULE, "_read_stdin", lambda: "not-json")

    exit_code = MODULE.main()

    assert exit_code == 2
    assert "invalid-input" in capsys.readouterr().out


def test_main_reraises_unexpected_runtime_error_from_parse_pr_checks(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(required_checks="workflow-lint"),
    )
    monkeypatch.setattr(MODULE, "_read_stdin", lambda: "[]")

    def _raise_runtime_error(_: str) -> NoReturn:
        raise RuntimeError("unexpected parse failure")

    monkeypatch.setattr(MODULE, "parse_pr_checks", _raise_runtime_error)

    with pytest.raises(RuntimeError, match="unexpected parse failure"):
        MODULE.main()

    assert "invalid-input" not in capsys.readouterr().out
