from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "scripts"
    / "review_checks"
    / "dependency_review_action_runtime_check.py"
)


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "dependency_review_action_runtime_check", SCRIPT_PATH
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


def test_defaults_monitor_mutable_upstream_ref() -> None:
    assert MODULE.MONITORED_ACTION_REF == "actions/dependency-review-action@v4"
    assert MODULE.MONITORED_ACTION_YAML_URL.endswith("/v4/action.yml")
    assert (
        "2031cfc080254a8a887f58cffee85186f0e49e48"
        not in MODULE.MONITORED_ACTION_YAML_URL
    )


def test_parse_runs_using_detects_node_runtime() -> None:
    action_yaml = """
name: Dependency Review Action
runs:
  using: 'node20'
  main: dist/index.js
"""

    assert MODULE.parse_runs_using(action_yaml) == "node20"


def test_parse_runs_using_handles_double_quotes() -> None:
    action_yaml = 'runs:\n  using: "node24"\n'

    assert MODULE.parse_runs_using(action_yaml) == "node24"


def test_evaluate_runtime_status_marks_expected_runtime_as_ready() -> None:
    result = MODULE.evaluate_runtime_status(
        action_ref="actions/dependency-review-action@deadbeef",
        expected_runtime="node24",
        actual_runtime="node24",
    )

    assert result.status == "ready"
    assert result.is_expected is True


def test_evaluate_runtime_status_marks_mismatch_as_monitoring() -> None:
    result = MODULE.evaluate_runtime_status(
        action_ref="actions/dependency-review-action@deadbeef",
        expected_runtime="node24",
        actual_runtime="node20",
    )

    assert result.status == "monitoring"
    assert result.is_expected is False


def test_main_returns_0_when_still_monitoring(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            action_ref="actions/dependency-review-action@deadbeef",
            action_yaml_url="https://example.invalid/action.yml",
            expected_runtime="node24",
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_action_yaml",
        lambda **_: "runs:\n  using: 'node20'\n",
    )

    exit_code = MODULE.main()

    assert exit_code == 0
    assert '"status": "monitoring"' in capsys.readouterr().out


def test_main_returns_1_when_runtime_is_ready(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            action_ref="actions/dependency-review-action@deadbeef",
            action_yaml_url="https://example.invalid/action.yml",
            expected_runtime="node24",
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_action_yaml",
        lambda **_: "runs:\n  using: 'node24'\n",
    )

    exit_code = MODULE.main()

    assert exit_code == 1
    assert '"status": "ready"' in capsys.readouterr().out


def test_main_returns_2_when_runtime_cannot_be_parsed(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            action_ref="actions/dependency-review-action@deadbeef",
            action_yaml_url="https://example.invalid/action.yml",
            expected_runtime="node24",
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_action_yaml",
        lambda **_: "runs:\n  main: dist/index.js\n",
    )

    exit_code = MODULE.main()

    assert exit_code == 2
    assert '"status": "parse-error"' in capsys.readouterr().out


def test_main_returns_2_on_unexpected_exception_with_structured_payload(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            action_ref="actions/dependency-review-action@v4",
            action_yaml_url="https://example.invalid/action.yml",
            expected_runtime="node24",
        ),
    )
    monkeypatch.setattr(
        MODULE,
        "fetch_action_yaml",
        lambda **_: "runs:\n  using: 'node20'\n",
    )

    def _raise(*, action_ref: str, expected_runtime: str, actual_runtime: str):
        _ = action_ref, expected_runtime, actual_runtime
        raise ValueError("boom")

    monkeypatch.setattr(MODULE, "evaluate_runtime_status", _raise)

    exit_code = MODULE.main()

    assert exit_code == 2
    assert '"status": "unexpected-error"' in capsys.readouterr().out
