"""Test module entrypoint."""

import runpy
import sys
from unittest.mock import patch

import pytest


def test_module_execution():
    """Ensure `python -m vector_topic_modeling` executes the CLI."""
    with (
        patch.object(sys, "argv", ["vector_topic_modeling", "cluster", "--help"]),
        patch("vector_topic_modeling.cli.main", return_value=0) as mock_main,
    ):
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("vector_topic_modeling", run_name="__main__")
        assert exc_info.value.code == 0
        mock_main.assert_called_once()


def test_module_import():
    """Ensure importing `__main__` does not execute main()."""
    with patch("vector_topic_modeling.cli.main") as mock_main:
        sys.modules.pop("vector_topic_modeling.__main__", None)
        import vector_topic_modeling.__main__  # noqa: F401

        mock_main.assert_not_called()
