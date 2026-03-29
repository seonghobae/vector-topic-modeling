from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def load_smoke_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "smoke_installed_cli.py"
    )
    spec = importlib.util.spec_from_file_location("smoke_installed_cli", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smoke = load_smoke_module()
build_smoke_commands = smoke.build_smoke_commands
resolve_venv_python = smoke.resolve_venv_python
select_built_wheel = smoke.select_built_wheel
venv_bin_dir = smoke.venv_bin_dir
venv_cli_name = smoke.venv_cli_name
venv_python_name = smoke.venv_python_name


def test_select_built_wheel_returns_matching_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "vector_topic_modeling-0.1.0-py3-none-any.whl"
    wheel.write_text("", encoding="utf-8")
    (tmp_path / "vector_topic_modeling-0.1.0.tar.gz").write_text("", encoding="utf-8")

    assert select_built_wheel(tmp_path) == wheel


def test_select_built_wheel_rejects_ambiguous_wheels(tmp_path: Path) -> None:
    (tmp_path / "vector_topic_modeling-0.1.0-py3-none-any.whl").write_text(
        "", encoding="utf-8"
    )
    (tmp_path / "vector_topic_modeling-0.1.1-py3-none-any.whl").write_text(
        "", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Expected exactly one wheel"):
        select_built_wheel(tmp_path)


def test_select_built_wheel_rejects_missing_wheels(tmp_path: Path) -> None:
    (tmp_path / "vector_topic_modeling-0.1.0.tar.gz").write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Expected exactly one wheel"):
        select_built_wheel(tmp_path)


def test_build_smoke_commands_cover_import_and_cli_entrypoint(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"

    commands = build_smoke_commands(bin_dir)

    assert commands[0][:3] == [
        str(bin_dir / "python"),
        "-m",
        "pip",
    ]
    assert commands[1][0] == str(bin_dir / "python")
    assert commands[2] == [
        str(bin_dir / "vector-topic-modeling"),
        "--help",
    ]
    assert commands[3] == [
        str(bin_dir / "vector-topic-modeling"),
        "cluster",
        "--help",
    ]
    assert commands[4] == [
        str(bin_dir / "python"),
        "-m",
        "vector_topic_modeling",
        "--help",
    ]
    assert commands[5] == [
        str(bin_dir / "python"),
        "-m",
        "vector_topic_modeling",
        "cluster",
        "--help",
    ]


def test_windows_smoke_commands_use_python_exe(tmp_path: Path) -> None:
    bin_dir = tmp_path / "Scripts"

    commands = build_smoke_commands(bin_dir, os_name="nt")

    assert commands[0][0] == str(bin_dir / "python.exe")
    assert commands[1][0] == str(bin_dir / "python.exe")


def test_windows_venv_paths_use_scripts_and_exe(tmp_path: Path) -> None:
    venv_dir = tmp_path / "venv"

    assert venv_bin_dir(venv_dir, os_name="nt") == venv_dir / "Scripts"
    assert venv_python_name(os_name="nt") == "python.exe"
    assert (
        venv_cli_name("vector-topic-modeling", os_name="nt")
        == "vector-topic-modeling.exe"
    )


def test_resolve_venv_python_prefers_explicit_value(monkeypatch) -> None:
    monkeypatch.setattr(smoke.shutil, "which", lambda _: None)

    assert resolve_venv_python("/tmp/python3.11") == "/tmp/python3.11"


def test_resolve_venv_python_prefers_python311_on_path_when_needed(
    monkeypatch,
) -> None:
    monkeypatch.setattr(smoke.sys, "executable", "/tmp/python3.10")
    monkeypatch.setattr(smoke.sys, "version_info", (3, 10, 0))
    monkeypatch.setattr(
        smoke.shutil,
        "which",
        lambda name: "/usr/local/bin/python3.11" if name == "python3.11" else None,
    )

    assert resolve_venv_python() == "/usr/local/bin/python3.11"


def test_resolve_venv_python_prefers_current_interpreter_when_supported(
    monkeypatch,
) -> None:
    monkeypatch.setattr(smoke.sys, "executable", "/tmp/current-python")
    monkeypatch.setattr(smoke.sys, "version_info", (3, 12, 0))
    monkeypatch.setattr(
        smoke.shutil,
        "which",
        lambda name: "/usr/local/bin/python3.11" if name == "python3.11" else None,
    )

    assert resolve_venv_python() == "/tmp/current-python"
