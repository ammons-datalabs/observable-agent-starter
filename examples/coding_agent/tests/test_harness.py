"""Tests for the coding agent harness."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from adl_agent.harness import (
    run_command,
    repo_snapshot,
    apply_patch,
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


class TestApplyPatch:
    """Tests for apply_patch function."""

    def test_apply_patch_success(self, tmp_path):
        """Test successful patch application."""
        # Create a temporary git repo
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo and create a file
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)

        test_file = repo / "test.txt"
        test_file.write_text("line 1\n")
        subprocess.run(["git", "add", "test.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True)

        # Create a valid patch
        patch = """--- a/test.txt
+++ b/test.txt
@@ -1 +1,2 @@
 line 1
+line 2
"""

        success, output = apply_patch(str(repo), patch)

        assert success is True
        assert (repo / "test.txt").read_text() == "line 1\nline 2\n"

    def test_apply_patch_invalid_patch(self, tmp_path):
        """Test that invalid patches are handled."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

        invalid_patch = "not a valid patch"

        success, output = apply_patch(str(repo), invalid_patch)

        assert success is False
        assert len(output) > 0  # Should have error message

    def test_apply_patch_cleans_up_temp_file(self, tmp_path):
        """Test that temporary patch file is cleaned up."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

        patch = "invalid patch"

        # Track temp files before
        temp_dir = Path(tempfile.gettempdir())
        before_count = len(list(temp_dir.glob("*.patch")))

        apply_patch(str(repo), patch)

        # Temp file should be cleaned up
        after_count = len(list(temp_dir.glob("*.patch")))
        assert after_count <= before_count


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
    @patch("adl_agent.harness.apply_patch")
    @patch("adl_agent.harness.format_lint_and_test")
    def test_make_patch_and_test_success(
        self, mock_format_lint, mock_apply, mock_snapshot
    ):
        """Test successful patch generation and testing."""
        mock_snapshot.return_value = "repo state"
        mock_apply.return_value = (True, "patch applied")
        mock_format_lint.return_value = (True, "all tests passed")

        # Mock agent
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.patch = "diff content"
        mock_result.explanation = "Added feature X"
        mock_result.risk_level = "low"
        mock_agent.forward.return_value = mock_result

        patch, tests_passed, output = make_patch_and_test(
            task="Add feature X",
            repo_path="/fake/repo",
            allow_globs=["src/**/*.py"],
            agent=mock_agent,
            dry_run=False,
        )

        assert patch == "diff content"
        assert tests_passed is True
        assert "Added feature X" in output
        assert "low" in output
        assert "all tests passed" in output

        # Verify agent was called correctly
        mock_agent.forward.assert_called_once_with(
            task="Add feature X",
            repo_state="repo state",
            allowed_patterns=["src/**/*.py"],
        )

    @patch("adl_agent.harness.repo_snapshot")
    def test_make_patch_and_test_agent_fails(self, mock_snapshot):
        """Test when agent fails to generate patch."""
        mock_snapshot.return_value = "repo state"

        mock_agent = Mock()
        mock_agent.forward.side_effect = ValueError("Patch modifies disallowed files")

        patch, tests_passed, output = make_patch_and_test(
            task="Bad task",
            repo_path="/fake/repo",
            allow_globs=["src/**/*.py"],
            agent=mock_agent,
        )

        assert patch == ""
        assert tests_passed is False
        assert "Agent failed to generate patch" in output
        assert "disallowed files" in output

    @patch("adl_agent.harness.repo_snapshot")
    def test_make_patch_and_test_dry_run(self, mock_snapshot):
        """Test dry run mode."""
        mock_snapshot.return_value = "repo state"

        mock_agent = Mock()
        mock_result = Mock()
        mock_result.patch = "diff content"
        mock_result.explanation = "Would add feature"
        mock_result.risk_level = "medium"
        mock_agent.forward.return_value = mock_result

        patch, tests_passed, output = make_patch_and_test(
            task="Add feature",
            repo_path="/fake/repo",
            allow_globs=["src/**/*.py"],
            agent=mock_agent,
            dry_run=True,
        )

        assert patch == "diff content"
        assert tests_passed is False  # Always False in dry run
        assert "DRY RUN" in output
        assert "Would add feature" in output
        assert "medium" in output

    @patch("adl_agent.harness.repo_snapshot")
    @patch("adl_agent.harness.apply_patch")
    def test_make_patch_and_test_patch_apply_fails(self, mock_apply, mock_snapshot):
        """Test when patch fails to apply."""
        mock_snapshot.return_value = "repo state"
        mock_apply.return_value = (False, "patch does not apply")

        mock_agent = Mock()
        mock_result = Mock()
        mock_result.patch = "bad diff"
        mock_result.explanation = "Added feature"
        mock_result.risk_level = "low"
        mock_agent.forward.return_value = mock_result

        patch, tests_passed, output = make_patch_and_test(
            task="Add feature",
            repo_path="/fake/repo",
            allow_globs=["src/**/*.py"],
            agent=mock_agent,
        )

        assert patch == "bad diff"
        assert tests_passed is False
        assert "Failed to apply patch" in output
        assert "patch does not apply" in output

    @patch("adl_agent.harness.repo_snapshot")
    @patch("adl_agent.harness.apply_patch")
    @patch("adl_agent.harness.format_lint_and_test")
    def test_make_patch_and_test_tests_fail(
        self, mock_format_lint, mock_apply, mock_snapshot
    ):
        """Test when tests fail after applying patch."""
        mock_snapshot.return_value = "repo state"
        mock_apply.return_value = (True, "patch applied")
        mock_format_lint.return_value = (False, "2 tests failed")

        mock_agent = Mock()
        mock_result = Mock()
        mock_result.patch = "diff content"
        mock_result.explanation = "Added feature"
        mock_result.risk_level = "high"
        mock_agent.forward.return_value = mock_result

        patch, tests_passed, output = make_patch_and_test(
            task="Add feature",
            repo_path="/fake/repo",
            allow_globs=["src/**/*.py"],
            agent=mock_agent,
        )

        assert patch == "diff content"
        assert tests_passed is False
        assert "2 tests failed" in output
        assert "high" in output
