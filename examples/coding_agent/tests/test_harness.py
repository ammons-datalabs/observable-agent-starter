"""Tests for the coding agent harness."""

import subprocess
from unittest.mock import Mock, patch
import pytest

from adl_agent.harness import (
    run_command,
    repo_snapshot,
    strip_markdown_fences,
    write_new_file,
    format_lint_and_test,
    make_patch_and_test,
)


class TestRunCommand:
    """Tests for run_command function."""

    def test_run_command_success(self):
        """Test successful command execution."""
        result = run_command(["echo", "hello"], cwd=".")
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_command_with_check_true_raises_on_failure(self):
        """Test that check=True raises CalledProcessError on failure."""
        with pytest.raises(subprocess.CalledProcessError):
            run_command(["false"], cwd=".", check=True)

    def test_run_command_with_check_false_returns_on_failure(self):
        """Test that check=False returns CompletedProcess even on failure."""
        result = run_command(["false"], cwd=".", check=False)
        assert result.returncode != 0
        assert isinstance(result, subprocess.CompletedProcess)

    def test_run_command_captures_output(self):
        """Test that stdout and stderr are captured."""
        result = run_command(["python", "-c", "print('out'); import sys; sys.stderr.write('err')"], cwd=".")
        assert "out" in result.stdout
        assert "err" in result.stderr


class TestRepoSnapshot:
    """Tests for repo_snapshot function."""

    @patch("adl_agent.harness.run_command")
    def test_repo_snapshot_success(self, mock_run_command):
        """Test successful repo snapshot capture."""
        # Mock git commands
        mock_run_command.side_effect = [
            Mock(stdout="file1.py\nfile2.py\n"),  # git ls-files
            Mock(stdout="diff content\n"),         # git diff
            Mock(stdout=" M file1.py\n"),          # git status
        ]

        snapshot = repo_snapshot("/fake/repo")

        assert "=== GIT FILES ===" in snapshot
        assert "file1.py" in snapshot
        assert "=== GIT DIFF ===" in snapshot
        assert "diff content" in snapshot
        assert "=== GIT STATUS ===" in snapshot

        # Verify calls
        assert mock_run_command.call_count == 3
        mock_run_command.assert_any_call(["git", "ls-files"], cwd="/fake/repo")
        mock_run_command.assert_any_call(["git", "diff"], cwd="/fake/repo", check=False)
        mock_run_command.assert_any_call(["git", "status", "--short"], cwd="/fake/repo", check=False)

    @patch("adl_agent.harness.run_command")
    def test_repo_snapshot_handles_error(self, mock_run_command):
        """Test that errors are caught and returned as error message."""
        mock_run_command.side_effect = Exception("Git command failed")

        snapshot = repo_snapshot("/fake/repo")

        assert "Error capturing repo state" in snapshot
        assert "Git command failed" in snapshot

    def test_repo_snapshot_includes_file_contents(self, tmp_path):
        """Test that repo snapshot includes actual file contents."""
        # Create a real git repo with files
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

        # Create test files
        (repo / "file1.py").write_text("def hello():\n    return 'world'\n")
        (repo / "file2.py").write_text("x = 42\n")

        # Add and commit
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "test"], cwd=repo, check=True)

        # Capture snapshot
        snapshot = repo_snapshot(str(repo))

        # Verify file contents are included
        assert "=== FILE CONTENTS ===" in snapshot
        assert "=== file1.py ===" in snapshot
        assert "def hello():" in snapshot
        assert "return 'world'" in snapshot
        assert "=== file2.py ===" in snapshot
        assert "x = 42" in snapshot


class TestStripMarkdownFences:
    """Tests for strip_markdown_fences function."""

    def test_strip_python_code_fences(self):
        """Test stripping Python code fences."""
        content = "```python\ndef hello():\n    return 'world'\n```"
        result = strip_markdown_fences(content)
        assert result == "def hello():\n    return 'world'"

    def test_strip_generic_code_fences(self):
        """Test stripping generic code fences."""
        content = "```\nx = 42\ny = 100\n```"
        result = strip_markdown_fences(content)
        assert result == "x = 42\ny = 100"

    def test_no_fences_returns_unchanged(self):
        """Test that content without fences is unchanged."""
        content = "def hello():\n    return 'world'"
        result = strip_markdown_fences(content)
        assert result == content

    def test_partial_fences_only_strips_if_both_present(self):
        """Test that only complete fence pairs are stripped."""
        # Only opening fence
        content = "```python\ndef hello():\n    return 'world'"
        result = strip_markdown_fences(content)
        # Should strip opening fence since no closing
        assert result == "def hello():\n    return 'world'"

    def test_empty_content(self):
        """Test handling of empty content."""
        result = strip_markdown_fences("")
        assert result == ""


class TestWriteNewFile:
    """Tests for write_new_file function."""

    def test_write_new_file_success(self, tmp_path):
        """Test successful file creation."""
        repo = tmp_path / "test_repo"
        repo.mkdir()

        content = "def hello():\n    return 'world'\n"
        success, output = write_new_file(str(repo), "utils.py", content)

        assert success is True
        assert (repo / "utils.py").read_text() == content
        assert "Created utils.py" in output

    def test_write_new_file_with_subdirectory(self, tmp_path):
        """Test file creation in subdirectory."""
        repo = tmp_path / "test_repo"
        repo.mkdir()

        content = "x = 42\n"
        success, output = write_new_file(str(repo), "src/helpers.py", content)

        assert success is True
        assert (repo / "src" / "helpers.py").read_text() == content
        assert "Created src/helpers.py" in output

    def test_write_new_file_already_exists(self, tmp_path):
        """Test that existing files are not overwritten."""
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Create the file first
        (repo / "test.py").write_text("original content")

        # Try to write it again
        success, output = write_new_file(str(repo), "test.py", "new content")

        assert success is False
        assert "already exists" in output
        assert (repo / "test.py").read_text() == "original content"

    def test_write_new_file_handles_errors(self, tmp_path):
        """Test that write errors are handled gracefully."""
        # Try to write to invalid path
        success, output = write_new_file("/invalid/path/that/does/not/exist", "test.py", "content")

        assert success is False
        assert "Failed to write file" in output

    def test_write_new_file_strips_markdown_fences(self, tmp_path):
        """Test that markdown code fences are automatically stripped."""
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Content with markdown fences (common LLM output)
        content_with_fences = "```python\ndef hello():\n    return 'world'\n```"
        success, output = write_new_file(str(repo), "utils.py", content_with_fences)

        assert success is True
        # File should NOT contain the markdown fences
        written_content = (repo / "utils.py").read_text()
        assert written_content == "def hello():\n    return 'world'"
        assert "```" not in written_content


class TestFormatLintAndTest:
    """Tests for format_lint_and_test function."""

    @patch("adl_agent.harness.run_command")
    def test_format_lint_and_test_all_pass(self, mock_run_command):
        """Test when all checks pass."""
        mock_run_command.side_effect = [
            Mock(returncode=0, stdout="All checks passed!", stderr=""),  # ruff
            Mock(returncode=0, stdout="5 passed", stderr=""),            # pytest
        ]

        all_passed, output = format_lint_and_test("/fake/repo")

        assert all_passed is True
        assert "✓" in output
        assert "Ruff linting" in output
        assert "Tests" in output
        assert "All checks passed!" in output

    @patch("adl_agent.harness.run_command")
    def test_format_lint_and_test_ruff_fails(self, mock_run_command):
        """Test when ruff fails."""
        mock_run_command.side_effect = [
            Mock(returncode=1, stdout="", stderr="Found 3 errors"),  # ruff fails
            Mock(returncode=0, stdout="5 passed", stderr=""),        # pytest passes
        ]

        all_passed, output = format_lint_and_test("/fake/repo")

        assert all_passed is False
        assert "✗" in output
        assert "Found 3 errors" in output

    @patch("adl_agent.harness.run_command")
    def test_format_lint_and_test_pytest_fails(self, mock_run_command):
        """Test when pytest fails."""
        mock_run_command.side_effect = [
            Mock(returncode=0, stdout="All checks passed!", stderr=""),  # ruff passes
            Mock(returncode=1, stdout="", stderr="2 failed, 3 passed"),  # pytest fails
        ]

        all_passed, output = format_lint_and_test("/fake/repo")

        assert all_passed is False
        assert "2 failed, 3 passed" in output

    @patch("adl_agent.harness.run_command")
    def test_format_lint_and_test_truncates_output(self, mock_run_command):
        """Test that output is truncated to 500 chars."""
        long_output = "x" * 1000
        mock_run_command.side_effect = [
            Mock(returncode=0, stdout=long_output, stderr=""),
            Mock(returncode=0, stdout=long_output, stderr=""),
        ]

        all_passed, output = format_lint_and_test("/fake/repo")

        # Each stdout is truncated to 500 chars in the results
        assert len(output) < len(long_output) * 2


class TestMakePatchAndTest:
    """Tests for make_patch_and_test function."""

    @patch("adl_agent.harness.repo_snapshot")
    @patch("adl_agent.harness.write_new_file")
    @patch("adl_agent.harness.format_lint_and_test")
    def test_make_patch_and_test_success(
        self, mock_format_lint, mock_write, mock_snapshot
    ):
        """Test successful file generation and testing."""
        mock_snapshot.return_value = "repo state"
        mock_write.return_value = (True, "file created")
        mock_format_lint.return_value = (True, "all tests passed")

        # Mock agent
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.filename = "utils.py"
        mock_result.content = "def hello():\n    return 'world'\n"
        mock_result.explanation = "Added utility functions"
        mock_result.risk_level = "low"
        mock_agent.return_value = mock_result

        content, tests_passed, output = make_patch_and_test(
            task="Add utility functions",
            repo_path="/fake/repo",
            allow_globs=["*.py"],
            agent=mock_agent,
            dry_run=False,
        )

        assert content == "def hello():\n    return 'world'\n"
        assert tests_passed is True
        assert "Added utility functions" in output
        assert "low" in output
        assert "all tests passed" in output

        # Verify agent was called correctly
        mock_agent.assert_called_once_with(
            task="Add utility functions",
            repo_state="repo state",
            allowed_patterns=["*.py"],
        )

    @patch("adl_agent.harness.repo_snapshot")
    def test_make_patch_and_test_agent_fails(self, mock_snapshot):
        """Test when agent fails to generate file."""
        mock_snapshot.return_value = "repo state"

        mock_agent = Mock()
        mock_agent.side_effect = ValueError("Filename does not match allowed patterns")

        content, tests_passed, output = make_patch_and_test(
            task="Bad task",
            repo_path="/fake/repo",
            allow_globs=["src/**/*.py"],
            agent=mock_agent,
        )

        assert content == ""
        assert tests_passed is False
        assert "Agent failed to generate file" in output
        assert "allowed patterns" in output

    @patch("adl_agent.harness.repo_snapshot")
    def test_make_patch_and_test_dry_run(self, mock_snapshot):
        """Test dry run mode."""
        mock_snapshot.return_value = "repo state"

        mock_agent = Mock()
        mock_result = Mock()
        mock_result.filename = "test.py"
        mock_result.content = "x = 42\n"
        mock_result.explanation = "Would add test file"
        mock_result.risk_level = "medium"
        mock_agent.return_value = mock_result

        content, tests_passed, output = make_patch_and_test(
            task="Add test file",
            repo_path="/fake/repo",
            allow_globs=["*.py"],
            agent=mock_agent,
            dry_run=True,
        )

        assert content == "x = 42\n"
        assert tests_passed is False  # Always False in dry run
        assert "DRY RUN" in output
        assert "Would add test file" in output
        assert "medium" in output

    @patch("adl_agent.harness.repo_snapshot")
    @patch("adl_agent.harness.write_new_file")
    def test_make_patch_and_test_write_fails(self, mock_write, mock_snapshot):
        """Test when file write fails."""
        mock_snapshot.return_value = "repo state"
        mock_write.return_value = (False, "file already exists")

        mock_agent = Mock()
        mock_result = Mock()
        mock_result.filename = "existing.py"
        mock_result.content = "new content"
        mock_result.explanation = "Added file"
        mock_result.risk_level = "low"
        mock_agent.return_value = mock_result

        content, tests_passed, output = make_patch_and_test(
            task="Add file",
            repo_path="/fake/repo",
            allow_globs=["*.py"],
            agent=mock_agent,
        )

        assert content == "new content"
        assert tests_passed is False
        assert "Failed to write file" in output
        assert "already exists" in output

    @patch("adl_agent.harness.repo_snapshot")
    @patch("adl_agent.harness.write_new_file")
    @patch("adl_agent.harness.format_lint_and_test")
    def test_make_patch_and_test_tests_fail(
        self, mock_format_lint, mock_write, mock_snapshot
    ):
        """Test when tests fail after writing file."""
        mock_snapshot.return_value = "repo state"
        mock_write.return_value = (True, "file created")
        mock_format_lint.return_value = (False, "2 tests failed")

        mock_agent = Mock()
        mock_result = Mock()
        mock_result.filename = "broken.py"
        mock_result.content = "def broken():\n    raise Exception()\n"
        mock_result.explanation = "Added broken function"
        mock_result.risk_level = "high"
        mock_agent.return_value = mock_result

        content, tests_passed, output = make_patch_and_test(
            task="Add function",
            repo_path="/fake/repo",
            allow_globs=["*.py"],
            agent=mock_agent,
        )

        assert content == "def broken():\n    raise Exception()\n"
        assert tests_passed is False
        assert "2 tests failed" in output
        assert "high" in output
