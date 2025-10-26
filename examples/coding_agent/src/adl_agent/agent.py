"""DSPy-based coding agent with structured outputs and guardrails.

Demonstrates extending BaseAgent from observable_agent_starter.
"""

import dspy
from langfuse import observe
from typing import List, Optional
from pathlib import Path
import re

from observable_agent_starter import BaseAgent


class CodePatch(dspy.Signature):
    """Generate a code patch for a given engineering task."""

    task: str = dspy.InputField(desc="Engineering task description")
    repo_state: str = dspy.InputField(desc="Current repository state (files + diff)")
    allowed_patterns: str = dspy.InputField(desc="Glob patterns for allowed files")

    patch: str = dspy.OutputField(desc="Unified diff patch (git format)")
    explanation: str = dspy.OutputField(desc="What changed and why")
    risk_level: str = dspy.OutputField(desc="Risk assessment: low, medium, or high")
    files_modified: str = dspy.OutputField(desc="Comma-separated list of modified files")


def extract_files_from_patch(patch: str) -> List[str]:
    """Extract file paths from a unified diff patch."""
    files = []
    for line in patch.split("\n"):
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            # Extract filename from diff headers
            file_path = line.split("/", 1)[1] if "/" in line else ""
            if file_path and file_path != "/dev/null":
                files.append(file_path)
    return list(set(files))


def validate_patch_files(allowed_patterns: List[str], patch_files: List[str]) -> bool:
    """Validate that all files in patch match allowed patterns."""
    import fnmatch

    # Use fnmatch which handles ** patterns like shells do
    # This works with both relative patterns (src/**/*.py) and
    # absolute-style patterns (examples/coding_agent/**/*.py)
    for file_path in patch_files:
        matched = any(
            fnmatch.fnmatch(file_path, pattern) or Path(file_path).match(pattern)
            for pattern in allowed_patterns
        )
        if not matched:
            return False
    return True


class CodeAgent(dspy.Module, BaseAgent):
    """Autonomous coding agent with guardrails.

    Extends BaseAgent to get automatic LM configuration and tracing helpers.
    """

    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="code-agent-generate")

        self.generate = dspy.ChainOfThought(CodePatch)

    @observe(name="code-agent-generate")
    def forward(self, task: str, repo_state: str, allowed_patterns: List[str]) -> dspy.Prediction:
        """Generate a code patch with guardrails."""

        # Join patterns for prompt
        patterns_str = "\n".join(allowed_patterns)

        # Generate patch
        result = self.generate(
            task=task,
            repo_state=repo_state,
            allowed_patterns=patterns_str
        )

        # Validate guardrails
        patch_files = extract_files_from_patch(result.patch)

        # Check file restrictions
        files_valid = validate_patch_files(allowed_patterns, patch_files)

        # Check risk level
        risk_valid = result.risk_level.lower() in ["low", "medium", "high"]

        # Check patch is not empty
        patch_valid = len(result.patch.strip()) > 0

        # Validate with assertions (guardrails)
        if not files_valid:
            raise ValueError(
                f"Patch modifies disallowed files. Allowed: {allowed_patterns}, Got: {patch_files}"
            )
        if not risk_valid:
            raise ValueError(
                f"Risk level must be low/medium/high, got: {result.risk_level}"
            )
        if not patch_valid:
            raise ValueError("Patch cannot be empty")

        # Log via BaseAgent helper (in addition to @observe decorator)
        self.log_generation(
            input_data={"task": task, "allowed_patterns": patterns_str},
            output_data={
                "patch_length": len(result.patch),
                "explanation": result.explanation,
                "risk_level": result.risk_level,
                "files_modified": patch_files
            }
        )

        return result
