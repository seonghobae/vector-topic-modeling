"""Smoke-test the built wheel and its CLI entrypoint."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def select_built_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.glob("vector_topic_modeling-*.whl"))
    if len(wheels) != 1:
        raise ValueError(
            f"Expected exactly one wheel in {dist_dir}, found {len(wheels)}"
        )
    return wheels[0]


def build_smoke_commands(bin_dir: Path, os_name: str = os.name) -> list[list[str]]:
    python_bin = str(bin_dir / venv_python_name(os_name=os_name))
    cli_bin = str(bin_dir / venv_cli_name("vector-topic-modeling", os_name=os_name))
    return [
        [python_bin, "-m", "pip", "install", "--upgrade", "pip"],
        [
            python_bin,
            "-c",
            "import vector_topic_modeling; print(vector_topic_modeling.__all__)",
        ],
        [cli_bin, "--help"],
        [cli_bin, "cluster", "--help"],
    ]


def venv_bin_dir(venv_dir: Path, os_name: str = os.name) -> Path:
    return venv_dir / ("Scripts" if os_name == "nt" else "bin")


def venv_cli_name(name: str, os_name: str = os.name) -> str:
    return f"{name}.exe" if os_name == "nt" else name


def venv_python_name(os_name: str = os.name) -> str:
    return venv_cli_name("python", os_name=os_name)


def resolve_venv_python(python_executable: str | None = None) -> str:
    if python_executable:
        return python_executable
    if sys.version_info >= (3, 11):
        return sys.executable
    python311 = shutil.which("python3.11")
    if python311:
        return python311
    raise RuntimeError("Python 3.11+ is required to create the smoke-test venv")


def create_virtualenv(venv_dir: Path, python_executable: str | None = None) -> Path:
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
    run_command([resolve_venv_python(python_executable), "-m", "venv", str(venv_dir)])
    return venv_bin_dir(venv_dir)


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def smoke_test_built_cli(
    dist_dir: Path, venv_dir: Path, python_executable: str | None = None
) -> None:
    wheel = select_built_wheel(dist_dir)
    bin_dir = create_virtualenv(venv_dir, python_executable=python_executable)
    commands = build_smoke_commands(bin_dir)
    python_bin = str(bin_dir / venv_python_name())
    run_command(commands[0])
    run_command([python_bin, "-m", "pip", "install", str(wheel)])
    for command in commands[1:]:
        run_command(command)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test the built vector-topic-modeling wheel and CLI"
    )
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--venv-dir", default=".venv-smoke-cli")
    parser.add_argument("--python-executable")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    smoke_test_built_cli(
        Path(args.dist_dir),
        Path(args.venv_dir),
        python_executable=args.python_executable,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
