"""Tests for the coding agent."""

import pytest
from adl_agent.agent import extract_files_from_patch, validate_patch_files


def test_extract_files_from_patch():
    """Test extracting file paths from a unified diff."""
    patch = """--- a/src/example.py
+++ b/src/example.py
@@ -1,3 +1,4 @@
+import os
 def hello():
     print("hello")
--- a/tests/test_example.py
+++ b/tests/test_example.py
@@ -1,2 +1,3 @@
+import pytest
 def test_hello():
     pass
"""
    files = extract_files_from_patch(patch)
    assert "src/example.py" in files
    assert "tests/test_example.py" in files
    assert len(files) == 2


def test_extract_files_empty_patch():
    """Test extracting files from an empty patch."""
    files = extract_files_from_patch("")
    assert files == []


def test_validate_patch_files_allowed():
    """Test validating patch files against allowed patterns."""
    allowed = ["src/**/*.py", "tests/**/*.py"]
    files = ["src/foo/example.py", "tests/unit/test_example.py"]

    assert validate_patch_files(allowed, files) is True


def test_validate_patch_files_disallowed():
    """Test rejecting files that don't match allowed patterns."""
    allowed = ["src/**/*.py"]
    files = ["src/example.py", "config/settings.yaml"]

    assert validate_patch_files(allowed, files) is False


def test_validate_patch_files_empty():
    """Test validating an empty file list."""
    allowed = ["src/**/*.py"]
    files = []

    assert validate_patch_files(allowed, files) is True
