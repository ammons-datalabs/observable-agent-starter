"""Tests for the coding agent CLI."""

import pytest
import sys
from unittest.mock import Mock, patch
import subprocess

from adl_agent.cli import setup_dspy, main


class TestSetupDSPy:
    """Tests for setup_dspy function."""

    @patch("adl_agent.cli.dspy")
    def test_setup_with_anthropic_model_and_key(self, mock_dspy, monkeypatch, capsys):
        """Test setup with Anthropic model and API key."""
        monkeypatch.setenv("OPENAI_MODEL", "anthropic/claude-3-5-sonnet")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.setenv("LANGFUSE_HOST", "https://test")

        setup_dspy()

        captured = capsys.readouterr()
        assert "🧠 Model: anthropic/claude-3-5-sonnet" in captured.out
        assert "📊 Tracing: Enabled (Langfuse)" in captured.out
        mock_dspy.LM.assert_called_once_with("anthropic/claude-3-5-sonnet")
        mock_dspy.configure.assert_called_once()

    @patch("adl_agent.cli.dspy")
    def test_setup_with_openai_model_and_key(self, mock_dspy, monkeypatch, capsys):
        """Test setup with OpenAI model and API key."""
        monkeypatch.setenv("OPENAI_MODEL", "openai/gpt-4o")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)

        setup_dspy()

        captured = capsys.readouterr()
        assert "🧠 Model: openai/gpt-4o" in captured.out
        assert "ℹ️  Note: Langfuse tracing not configured" in captured.out
        mock_dspy.LM.assert_called_once_with("openai/gpt-4o")

    @patch("adl_agent.cli.dspy")
    def test_setup_with_gpt_model_requires_openai_key(self, mock_dspy, monkeypatch):
        """Test that gpt-* models require OPENAI_API_KEY."""
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            setup_dspy()

        assert exc_info.value.code == 1

    @patch("adl_agent.cli.dspy")
    def test_setup_with_anthropic_model_missing_key_exits(self, mock_dspy, monkeypatch, capsys):
        """Test that Anthropic model without key exits with error."""
        monkeypatch.setenv("OPENAI_MODEL", "anthropic/claude-3-5-sonnet")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            setup_dspy()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Error: ANTHROPIC_API_KEY not set" in captured.out

    @patch("adl_agent.cli.dspy")
    def test_setup_with_openai_model_missing_key_exits(self, mock_dspy, monkeypatch, capsys):
        """Test that OpenAI model without key exits with error."""
        monkeypatch.setenv("OPENAI_MODEL", "openai/gpt-4o")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            setup_dspy()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Error: OPENAI_API_KEY not set" in captured.out

    @patch("adl_agent.cli.dspy")
    def test_setup_with_unknown_model_warns(self, mock_dspy, monkeypatch, capsys):
        """Test that unknown model shows warning."""
        monkeypatch.setenv("OPENAI_MODEL", "unknown/model")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        setup_dspy()

        captured = capsys.readouterr()
        assert "⚠️  Warning: No API keys found" in captured.out

    @patch("adl_agent.cli.dspy")
    def test_setup_defaults_to_gpt_4o_mini(self, mock_dspy, monkeypatch):
        """Test that default model is gpt-4o-mini."""
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        setup_dspy()

        mock_dspy.LM.assert_called_once_with("gpt-4o-mini")


class TestMain:
    """Tests for main function."""

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_main_with_valid_args_dry_run(
        self, mock_agent_class, mock_setup, mock_run_cmd, mock_make_patch, tmp_path, monkeypatch
    ):
        """Test main with valid arguments in dry-run mode."""
        # Create temp git repo
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        # Mock git commands
        mock_run_cmd.return_value = Mock(stdout="main\n")

        # Mock agent
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        # Mock patch generation
        mock_make_patch.return_value = ("patch content", False, "dry run output")

        # Set CLI args
        test_args = ["adl-agent", "Add feature", "--repo", str(repo), "--dry-run"]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        mock_setup.assert_called_once()
        mock_agent_class.assert_called_once()
        mock_make_patch.assert_called_once()

    @patch("sys.argv", ["adl-agent"])
    def test_main_without_task_exits(self):
        """Test that missing task argument causes exit."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2  # argparse error code

    @patch("sys.argv", ["adl-agent", "task"])
    def test_main_without_repo_exits(self):
        """Test that missing --repo argument causes exit."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2  # argparse error code

    @patch("sys.argv", ["adl-agent", "--version"])
    def test_main_version_flag(self):
        """Test --version flag."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("sys.argv", ["adl-agent", "task", "--repo", "/nonexistent"])
    def test_main_nonexistent_repo_exits(self, capsys):
        """Test that nonexistent repo causes exit."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Error:" in captured.out
        assert "not a git repository" in captured.out

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_main_no_patch_generated_exits(
        self,
        mock_agent_class,
        mock_setup,
        mock_run_cmd,
        mock_make_patch,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        """Test that no patch generated causes exit."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        mock_run_cmd.return_value = Mock(stdout="main\n")
        mock_make_patch.return_value = ("", False, "error output")

        test_args = ["adl-agent", "task", "--repo", str(repo)]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "❌ No patch generated" in captured.out

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_main_tests_failed_exits(
        self,
        mock_agent_class,
        mock_setup,
        mock_run_cmd,
        mock_make_patch,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        """Test that failed tests cause exit."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        mock_run_cmd.return_value = Mock(stdout="main\n")
        mock_make_patch.return_value = ("patch", False, "tests failed output")

        test_args = ["adl-agent", "task", "--repo", str(repo)]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "❌ Tests failed" in captured.out


class TestBranchHandling:
    """Tests for branch name sanitization and creation."""

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_branch_name_sanitization(
        self, mock_agent_class, mock_setup, mock_run_cmd, mock_make_patch, tmp_path, monkeypatch
    ):
        """Test that branch names are sanitized."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        # Track git checkout calls
        checkout_calls = []

        def track_checkout(cmd, cwd):
            checkout_calls.append(cmd)
            if cmd[0] == "git" and cmd[1] == "checkout":
                # Simulate successful checkout
                return Mock(stdout="", returncode=0)
            return Mock(stdout="main\n")

        mock_run_cmd.side_effect = track_checkout
        mock_make_patch.return_value = ("patch", False, "output")

        # Task with special characters
        test_args = ["adl-agent", "Add feature: fix bug! @user", "--repo", str(repo), "--dry-run"]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit):
            main()

        # Find the checkout -b call
        checkout_branch_call = [c for c in checkout_calls if "-b" in c][0]
        branch_name = checkout_branch_call[3]

        # Should remove special characters
        assert ":" not in branch_name
        assert "!" not in branch_name
        assert "@" not in branch_name
        assert "agent/" in branch_name

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_branch_name_truncation(
        self, mock_agent_class, mock_setup, mock_run_cmd, mock_make_patch, tmp_path, monkeypatch
    ):
        """Test that long branch names are truncated."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        checkout_calls = []

        def track_checkout(cmd, cwd):
            checkout_calls.append(cmd)
            if cmd[0] == "git" and cmd[1] == "checkout":
                return Mock(stdout="", returncode=0)
            return Mock(stdout="main\n")

        mock_run_cmd.side_effect = track_checkout
        mock_make_patch.return_value = ("patch", False, "output")

        # Very long task name
        long_task = "Add " + "very " * 50 + "long feature"
        test_args = ["adl-agent", long_task, "--repo", str(repo), "--dry-run"]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit):
            main()

        checkout_branch_call = [c for c in checkout_calls if "-b" in c][0]
        branch_name = checkout_branch_call[3]

        # Total length should be prefix + "/" + sanitized (max 50 chars) = ~57 chars
        assert len(branch_name) <= 60

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_existing_branch_checkout(
        self,
        mock_agent_class,
        mock_setup,
        mock_run_cmd,
        mock_make_patch,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        """Test that existing branch is checked out."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        def checkout_behavior(cmd, cwd):
            if cmd[0] == "git" and cmd[1] == "checkout" and "-b" in cmd:
                # First checkout -b fails (branch exists)
                raise subprocess.CalledProcessError(1, cmd)
            elif cmd[0] == "git" and cmd[1] == "checkout":
                # Second checkout succeeds
                return Mock(stdout="", returncode=0)
            return Mock(stdout="main\n")

        mock_run_cmd.side_effect = checkout_behavior
        mock_make_patch.return_value = ("patch", False, "output")

        test_args = ["adl-agent", "task", "--repo", str(repo), "--dry-run"]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "⚠️  Branch already exists, checked it out" in captured.out


class TestArgumentParsing:
    """Tests for argument parsing."""

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_custom_allow_patterns(
        self, mock_agent_class, mock_setup, mock_run_cmd, mock_make_patch, tmp_path, monkeypatch
    ):
        """Test custom --allow patterns."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        mock_run_cmd.return_value = Mock(stdout="main\n")
        mock_make_patch.return_value = ("patch", False, "output")

        test_args = [
            "adl-agent",
            "task",
            "--repo",
            str(repo),
            "--allow",
            "src/**/*.py",
            "lib/**/*.py",
            "--dry-run",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit):
            main()

        # Check that custom patterns were passed
        call_args = mock_make_patch.call_args
        assert call_args[1]["allow_globs"] == ["src/**/*.py", "lib/**/*.py"]

    @patch("adl_agent.cli.make_patch_and_test")
    @patch("adl_agent.cli.run_command")
    @patch("adl_agent.cli.setup_dspy")
    @patch("adl_agent.cli.CodeAgent")
    def test_custom_branch_prefix(
        self, mock_agent_class, mock_setup, mock_run_cmd, mock_make_patch, tmp_path, monkeypatch
    ):
        """Test custom --branch-prefix."""
        repo = tmp_path / "test_repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        checkout_calls = []

        def track_checkout(cmd, cwd):
            checkout_calls.append(cmd)
            if cmd[0] == "git" and cmd[1] == "checkout":
                return Mock(stdout="", returncode=0)
            return Mock(stdout="main\n")

        mock_run_cmd.side_effect = track_checkout
        mock_make_patch.return_value = ("patch", False, "output")

        test_args = [
            "adl-agent",
            "task",
            "--repo",
            str(repo),
            "--branch-prefix",
            "feature",
            "--dry-run",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit):
            main()

        checkout_branch_call = [c for c in checkout_calls if "-b" in c][0]
        branch_name = checkout_branch_call[3]
        assert branch_name.startswith("feature/")
