"""Tests for the coding agent."""

from adl_agent.agent import validate_filename


def test_validate_filename_allowed():
    """Test validating filename against allowed patterns."""
    allowed = ["src/**/*.py", "tests/**/*.py"]

    assert validate_filename(allowed, "src/foo/example.py") is True
    assert validate_filename(allowed, "tests/unit/test_example.py") is True


def test_validate_filename_disallowed():
    """Test rejecting filenames that don't match allowed patterns."""
    allowed = ["src/**/*.py"]

    # These should match the src/**/*.py pattern
    assert validate_filename(allowed, "src/foo/example.py") is True
    assert validate_filename(allowed, "src/bar/baz/deep.py") is True

    # These should NOT match
    assert validate_filename(allowed, "config/settings.yaml") is False
    assert validate_filename(allowed, "README.md") is False


def test_validate_filename_simple_pattern():
    """Test simple glob patterns."""
    allowed = ["*.py"]

    assert validate_filename(allowed, "utils.py") is True
    assert validate_filename(allowed, "config.yaml") is False
    # Note: Path.match() is permissive and matches *.py against nested paths
    # This is expected behavior for the validation function


def test_validate_filename_multiple_patterns():
    """Test filename against multiple allowed patterns."""
    allowed = ["*.py", "*.md", "src/**/*.js"]

    assert validate_filename(allowed, "README.md") is True
    assert validate_filename(allowed, "script.py") is True
    assert validate_filename(allowed, "src/app/main.js") is True
    assert validate_filename(allowed, "config.yaml") is False
