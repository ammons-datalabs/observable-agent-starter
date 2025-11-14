"""Tests for CLI module."""

import pytest

from observable_agent_starter import __version__
from observable_agent_starter.cli import main


def test_cli_version(capsys):
    """Test --version flag displays version and exits successfully."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_cli_default_behavior(capsys):
    """Test default CLI behavior with no arguments."""
    result = main([])

    assert result == 0
    captured = capsys.readouterr()
    assert "observable-agent" in captured.out
    assert __version__ in captured.out
    assert "Ready" in captured.out


def test_cli_main_entrypoint():
    """Test that CLI can be invoked as main entrypoint."""
    # Verify the main function exists and is callable
    assert callable(main)
    assert main.__doc__ == "CLI entry point."
