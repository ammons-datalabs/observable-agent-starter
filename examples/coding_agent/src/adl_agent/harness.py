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

        # Also capture file contents for context (limit to reasonable size)
        file_contents = []
        for file_path in files.strip().split("\n"):
            if file_path:
                try:
                    full_path = pathlib.Path(repo_path) / file_path
                    if full_path.exists() and full_path.stat().st_size < 50000:  # Skip files > 50KB
                        content = full_path.read_text()
                        file_contents.append(f"=== {file_path} ===\n{content}")
                except Exception:
                    pass  # Skip files that can't be read

        contents_section = "\n\n".join(file_contents) if file_contents else "(no readable files)"

        snapshot = f"""=== GIT FILES ===
{files}

=== GIT DIFF ===
{diff}

=== GIT STATUS ===
{status}

=== FILE CONTENTS ===
{contents_section}
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


def strip_markdown_fences(content: str) -> str:
    """Remove markdown code fences if present."""
    lines = content.split('\n')

    # Check if content starts with markdown code fence
    if lines and lines[0].strip().startswith('```'):
        # Remove first line
        lines = lines[1:]

        # Check if content ends with markdown code fence
        if lines and lines[-1].strip() == '```':
            # Remove last line
            lines = lines[:-1]

    return '\n'.join(lines)


@observe(name="write-new-file")
def write_new_file(repo_path: str, filename: str, content: str) -> Tuple[bool, str]:
    """Write a new file to the repository."""
    try:
        file_path = pathlib.Path(repo_path) / filename

        # Check if file already exists
        if file_path.exists():
            return False, f"File {filename} already exists"

        # Strip markdown code fences if present (common LLM behavior)
        cleaned_content = strip_markdown_fences(content)

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        file_path.write_text(cleaned_content)

        return True, f"Created {filename} ({len(cleaned_content)} bytes)"
    except Exception as e:
        return False, f"Failed to write file: {e}"


@observe(name="make-file-and-test")
def make_patch_and_test(
    task: str,
    repo_path: str,
    allow_globs: List[str],
    agent,
    dry_run: bool = False
) -> Tuple[str, bool, str]:
    """
    Generate a new file using the agent and test it.

    Returns:
        (file_content, tests_passed, output_log)
    """
    # Capture repo state
    repo_state = repo_snapshot(repo_path)

    # Generate file with agent
    try:
        result = agent(
            task=task,
            repo_state=repo_state,
            allowed_patterns=allow_globs
        )
        filename = result.filename
        content = result.content
        explanation = result.explanation
        risk_level = result.risk_level
    except Exception as e:
        error_msg = f"Agent failed to generate file: {e}"
        return "", False, error_msg

    if dry_run:
        return content, False, f"DRY RUN - File generated but not written.\n\nFilename: {filename}\nExplanation: {explanation}\nRisk: {risk_level}"

    # Write file
    written, write_output = write_new_file(repo_path, filename, content)
    if not written:
        return content, False, f"Failed to write file:\n{write_output}"

    # Run tests
    tests_passed, test_output = format_lint_and_test(repo_path)

    output = f"""
=== FILE CREATED ===
Filename: {filename}
Explanation: {explanation}
Risk Level: {risk_level}

=== TEST RESULTS ===
{test_output}
"""

    return content, tests_passed, output
