"""Agent harness for executing code patches with testing."""

import subprocess
import pathlib
from typing import Tuple, List
from langfuse import observe


def run_command(cmd: List[str], cwd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


@observe(name="repo-snapshot")
def repo_snapshot(repo_path: str) -> str:
    """Capture the current state of the repository."""
    try:
        files = run_command(["git", "ls-files"], cwd=repo_path).stdout
        diff = run_command(["git", "diff"], cwd=repo_path, check=False).stdout
        status = run_command(["git", "status", "--short"], cwd=repo_path, check=False).stdout

        snapshot = f"""=== GIT FILES ===
{files}

=== GIT DIFF ===
{diff}

=== GIT STATUS ===
{status}
"""
        return snapshot
    except Exception as e:
        return f"Error capturing repo state: {e}"


@observe(name="format-lint-test")
def format_lint_and_test(repo_path: str) -> Tuple[bool, str]:
    """Run formatting, linting, and tests on the repository."""
    results = []
    all_passed = True

    checks = [
        (["ruff", "check", "."], "Ruff linting"),
        (["python", "-m", "pytest", "-q"], "Tests"),
    ]

    for cmd, name in checks:
        result = run_command(cmd, cwd=repo_path, check=False)
        passed = result.returncode == 0
        all_passed = all_passed and passed

        results.append({
            "name": name,
            "passed": passed,
            "stdout": result.stdout[:500],  # Truncate for logging
            "stderr": result.stderr[:500]
        })

    output = "\n\n".join([
        f"[{'✓' if r['passed'] else '✗'}] {r['name']}\n{r['stdout']}\n{r['stderr']}"
        for r in results
    ])

    return all_passed, output


@observe(name="apply-patch")
def apply_patch(repo_path: str, patch: str) -> Tuple[bool, str]:
    """Apply a git patch to the repository."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch)
        patch_file = f.name

    try:
        result = run_command(["git", "apply", patch_file], cwd=repo_path, check=False)
        success = result.returncode == 0

        return success, result.stdout + result.stderr
    finally:
        pathlib.Path(patch_file).unlink(missing_ok=True)


@observe(name="make-patch-and-test")
def make_patch_and_test(
    task: str,
    repo_path: str,
    allow_globs: List[str],
    agent,
    dry_run: bool = False
) -> Tuple[str, bool, str]:
    """
    Generate a patch using the agent and test it.

    Returns:
        (patch_text, tests_passed, output_log)
    """
    # Capture repo state
    repo_state = repo_snapshot(repo_path)

    # Generate patch with agent
    try:
        result = agent.forward(
            task=task,
            repo_state=repo_state,
            allowed_patterns=allow_globs
        )
        patch = result.patch
        explanation = result.explanation
        risk_level = result.risk_level
    except Exception as e:
        error_msg = f"Agent failed to generate patch: {e}"
        return "", False, error_msg

    if dry_run:
        return patch, False, f"DRY RUN - Patch generated but not applied.\n\nExplanation: {explanation}\nRisk: {risk_level}"

    # Apply patch
    applied, apply_output = apply_patch(repo_path, patch)
    if not applied:
        return patch, False, f"Failed to apply patch:\n{apply_output}"

    # Run tests
    tests_passed, test_output = format_lint_and_test(repo_path)

    output = f"""
=== PATCH APPLIED ===
Explanation: {explanation}
Risk Level: {risk_level}

=== TEST RESULTS ===
{test_output}
"""

    return patch, tests_passed, output
