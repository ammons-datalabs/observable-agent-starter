"""DSPy-based coding agent with structured outputs and guardrails.

Demonstrates extending BaseAgent from observable_agent_starter.
"""

import dspy
from langfuse import observe
from typing import List
from pathlib import Path

from observable_agent_starter import BaseAgent


class CodePatch(dspy.Signature):
    """Generate a new code file for a given engineering task."""

    task: str = dspy.InputField(desc="Engineering task description")
    repo_state: str = dspy.InputField(desc="Current repository state (files + diff)")
    allowed_patterns: str = dspy.InputField(desc="Glob patterns for allowed files")

    filename: str = dspy.OutputField(
        desc="Name of the file to create (e.g., 'utils.py' or 'src/helpers.py'). "
        "Must be a relative path from repository root."
    )
    content: str = dspy.OutputField(
        desc="Complete contents of the new file. Include all necessary imports, "
        "docstrings, and implementation. "
        "IMPORTANT: Output ONLY the raw file content, NO markdown formatting, "
        "NO code fences (```), NO extra backticks - just the actual Python code."
    )
    explanation: str = dspy.OutputField(desc="What the file does and why it's needed")
    risk_level: str = dspy.OutputField(desc="Risk assessment: low, medium, or high")


def validate_filename(allowed_patterns: List[str], filename: str) -> bool:
    """Validate that filename matches allowed patterns."""
    import fnmatch

    # Use fnmatch which handles ** patterns like shells do
    # This works with both relative patterns (src/**/*.py) and
    # absolute-style patterns (examples/coding_agent/**/*.py)
    matched = any(
        fnmatch.fnmatch(filename, pattern) or Path(filename).match(pattern)
        for pattern in allowed_patterns
    )
    return matched


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
        """Generate a new file with guardrails."""

        # Join patterns for prompt
        patterns_str = "\n".join(allowed_patterns)

        # Generate file
        result = self.generate(
            task=task,
            repo_state=repo_state,
            allowed_patterns=patterns_str
        )

        # Validate guardrails
        # Check file restrictions
        filename_valid = validate_filename(allowed_patterns, result.filename)

        # Check risk level
        risk_valid = result.risk_level.lower() in ["low", "medium", "high"]

        # Check content is not empty
        content_valid = len(result.content.strip()) > 0

        # Check filename is not empty
        filename_not_empty = len(result.filename.strip()) > 0

        # Validate with assertions (guardrails)
        if not filename_not_empty:
            raise ValueError("Filename cannot be empty")
        if not filename_valid:
            raise ValueError(
                f"Filename does not match allowed patterns. Allowed: {allowed_patterns}, Got: {result.filename}"
            )
        if not risk_valid:
            raise ValueError(
                f"Risk level must be low/medium/high, got: {result.risk_level}"
            )
        if not content_valid:
            raise ValueError("File content cannot be empty")

        # Log via BaseAgent helper (in addition to @observe decorator)
        self.log_generation(
            input_data={"task": task, "allowed_patterns": patterns_str},
            output_data={
                "filename": result.filename,
                "content_length": len(result.content),
                "explanation": result.explanation,
                "risk_level": result.risk_level
            }
        )

        return result
