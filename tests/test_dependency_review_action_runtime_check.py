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
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - defensive guard for loader failures
        sys.modules.pop(spec.name, None)
        raise RuntimeError(
            f"Failed to import module from {SCRIPT_PATH}: {exc}"
        ) from exc
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


def test_parse_runs_using_handles_inline_comment() -> None:
    action_yaml = "runs:\n  using: node24 # current runtime\n"

    assert MODULE.parse_runs_using(action_yaml) == "node24"


def test_parse_runs_using_ignores_block_scalar_content() -> None:
    action_yaml = (
        "runs:\n  pre: |\n    using: node18\n  using: node24\n  main: dist/index.js\n"
    )

    assert MODULE.parse_runs_using(action_yaml) == "node24"


def test_parse_runs_using_ignores_nested_using_key_under_runs_steps() -> None:
    action_yaml = (
        "runs:\n"
        "  steps:\n"
        "    - name: Example\n"
        "      with:\n"
        "        using: node999\n"
        "  main: dist/index.js\n"
    )

    assert MODULE.parse_runs_using(action_yaml) is None


def test_parse_runs_using_prefers_top_level_runs_using_over_nested_using() -> None:
    action_yaml = (
        "runs:\n"
        "  steps:\n"
        "    - name: Example\n"
        "      with:\n"
        "        using: node999\n"
        "  using: node24\n"
        "  main: dist/index.js\n"
    )

    assert MODULE.parse_runs_using(action_yaml) == "node24"


def test_parse_runs_using_returns_none_when_runs_has_no_using() -> None:
    action_yaml = "runs:\n  main: dist/index.js\n"

    assert MODULE.parse_runs_using(action_yaml) is None


def test_fetch_action_yaml_rejects_untrusted_url() -> None:
    try:
        MODULE.fetch_action_yaml(action_yaml_url="https://example.com/action.yml")
    except RuntimeError as err:
        message = str(err)
    else:
        raise AssertionError("expected RuntimeError")

    assert message == "action_yaml_url must use https://raw.githubusercontent.com"


def test_fetch_action_yaml_rejects_unexpected_raw_path() -> None:
    try:
        MODULE.fetch_action_yaml(
            action_yaml_url="https://raw.githubusercontent.com/owner/repo/main/action.yml"
        )
    except RuntimeError as err:
        message = str(err)
    else:
        raise AssertionError("expected RuntimeError")

    assert "must target /actions/dependency-review-action/<ref>/action.yml" in message


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


def test_main_returns_2_when_fetch_fails(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: SimpleNamespace(
            action_ref="actions/dependency-review-action@v4",
            action_yaml_url="https://example.invalid/action.yml",
            expected_runtime="node24",
        ),
    )

    def _raise_fetch(*, action_yaml_url: str) -> str:
        _ = action_yaml_url
        raise RuntimeError("failed to fetch action metadata")

    monkeypatch.setattr(MODULE, "fetch_action_yaml", _raise_fetch)

    exit_code = MODULE.main()

    assert exit_code == 2
    assert '"status": "fetch-error"' in capsys.readouterr().out


def test_main_returns_2_when_fetch_raises_non_runtime_error(
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

    def _raise_fetch(*, action_yaml_url: str) -> str:
        _ = action_yaml_url
        raise ValueError("unexpected")

    monkeypatch.setattr(MODULE, "fetch_action_yaml", _raise_fetch)

    exit_code = MODULE.main()

    assert exit_code == 2
    assert '"status": "fetch-error"' in capsys.readouterr().out


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
