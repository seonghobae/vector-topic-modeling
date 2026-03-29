"""Test module entrypoint."""

import runpy
import sys
from unittest.mock import patch


def test_module_execution():
    """Ensure `python -m vector_topic_modeling` executes the CLI."""
    with (
        patch.object(sys, "argv", ["vector_topic_modeling", "cluster", "--help"]),
        patch("vector_topic_modeling.cli.main", return_value=0) as mock_main,
    ):
        try:
            runpy.run_module("vector_topic_modeling", run_name="__main__")
        except SystemExit as e:
            assert e.code == 0
        mock_main.assert_called_once()


def test_module_import():
    """Ensure importing `__main__` does not execute main()."""
    with patch("vector_topic_modeling.cli.main") as mock_main:
        import vector_topic_modeling.__main__  # noqa: F401

        mock_main.assert_not_called()
