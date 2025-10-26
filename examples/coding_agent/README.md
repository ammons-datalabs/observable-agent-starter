# ADL Coding Agent

An autonomous coding agent that generates code patches with built-in observability, testing, and guardrails.

## Extending BaseAgent

This example demonstrates extending `observable_agent_starter.BaseAgent`:

```python
from observable_agent_starter import BaseAgent
import dspy

class CodeAgent(dspy.Module, BaseAgent):
    """Autonomous coding agent with guardrails."""

    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="code-agent-generate")

        # Your agent setup
        self.generate = dspy.ChainOfThought(CodePatch)
```

**What BaseAgent provides:**
- Automatic LM configuration from environment variables
- Langfuse tracing helper (`self.log_generation()`)
- Logging infrastructure

**What this example adds:**
- DSPy signatures for code generation
- Guardrails and validation logic (file restrictions, risk assessment)
- Git integration and PR workflow
- Operational quality gates (lint, tests, type-check)

## Features

- **DSPy-based Agent** - Structured code generation with Chain-of-Thought reasoning
- **Langfuse Tracing** - Full observability of agent decisions and patch generation
- **Guardrails** - File pattern restrictions and risk assessment via DSPy assertions
- **Automated Testing** - Runs linting and tests before committing
- **Git Integration** - Creates branches, commits, and optionally opens PRs

## Architecture

```
Task Input
    ↓
CodeAgent (DSPy ChainOfThought)
    ↓
Generate Patch (traced in Langfuse)
    ↓
Guardrails Check (DSPy Assertions)
    ├─ File pattern validation
    ├─ Risk level assessment
    └─ Patch validity check
    ↓
Apply Patch
    ↓
Run Tests (ruff + pytest)
    ↓
Commit + Optional PR
```

## Installation

```bash
cd examples/coding_agent
pip install -e .
```

## Usage

### Basic Usage

```bash
export OPENAI_API_KEY=your-key
export OPENAI_MODEL=gpt-4o-mini  # optional

adl-agent "Add docstrings to all public functions" \
  --repo /path/to/your/repo \
  --allow "src/**/*.py" "tests/**/*.py"
```

### Dry Run (generate patch without applying)

```bash
adl-agent "Refactor error handling" \
  --repo /path/to/your/repo \
  --dry-run
```

### Open PR Automatically

```bash
adl-agent "Add type hints to calculate_total function" \
  --repo /path/to/your/repo \
  --open-pr  # requires gh CLI
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key (required)
- `OPENAI_MODEL` - Model to use (default: `gpt-4o-mini`)
- `LANGFUSE_PUBLIC_KEY` - Langfuse public key (optional, for tracing)
- `LANGFUSE_SECRET_KEY` - Langfuse secret key (optional)
- `LANGFUSE_HOST` - Langfuse host (optional, default: `https://cloud.langfuse.com`)

### CLI Options

```
adl-agent <task> --repo <path> [options]

Options:
  --allow PATTERNS     Glob patterns for allowed files (default: src/**/*.py tests/**/*.py)
  --branch-prefix STR  Branch name prefix (default: agent)
  --dry-run           Generate patch but don't apply
  --open-pr           Create and push PR (requires gh CLI auth)
```

## DSPy Integration

The agent uses DSPy for structured code generation:

```python
class CodePatch(dspy.Signature):
    """Generate a code patch for a given engineering task."""

    task: str = dspy.InputField(desc="Engineering task description")
    repo_state: str = dspy.InputField(desc="Current repository state")
    allowed_patterns: str = dspy.InputField(desc="Glob patterns for allowed files")

    patch: str = dspy.OutputField(desc="Unified diff patch")
    explanation: str = dspy.OutputField(desc="What changed and why")
    risk_level: str = dspy.OutputField(desc="Risk assessment: low/medium/high")
    files_modified: str = dspy.OutputField(desc="Comma-separated list of files")
```

### Guardrails with DSPy Assertions

```python
# Ensure patch only modifies allowed files
dspy.Assert(
    validate_patch_files(allowed_patterns, patch_files),
    f"Patch modifies disallowed files. Allowed: {allowed_patterns}"
)

# Validate risk assessment
dspy.Assert(
    result.risk_level.lower() in ["low", "medium", "high"],
    f"Risk level must be low/medium/high, got: {result.risk_level}"
)
```

## Langfuse Tracing

Every agent run creates a trace in Langfuse with:

- **Task metadata** - Task description, repository, allowed patterns
- **Repo snapshot** - Files, diffs, status
- **Patch generation** - Includes explanation, risk level, files modified
- **Guardrail validation** - Each check logged with pass/fail
- **Test results** - Ruff linting and pytest outputs

View traces in your Langfuse dashboard under the `code-agent-run` observation.

## Example Traces

When you run the agent, you'll see full traceability:

```
code-agent-run (trace)
  ├─ repo-snapshot (span)
  ├─ code-agent-generate (span)
  │   ├─ generate-patch (span)
  │   └─ validate-guardrails (span)
  ├─ apply-patch (span)
  └─ format-lint-test (span)
```

## Testing

```bash
# Run agent tests
pytest tests/

# Test the agent in dry-run mode
adl-agent "Add logging to error paths" \
  --repo /path/to/test/repo \
  --dry-run
```

## Safety & Guardrails

The agent includes multiple safety mechanisms:

1. **File Restrictions** - Only modifies files matching allowed patterns
2. **Risk Assessment** - Agent evaluates risk level (low/medium/high)
3. **Automated Testing** - Runs linting and tests before committing
4. **Git Isolation** - Works on separate branches
5. **Manual Review** - Failed tests leave branch for manual inspection

## Demo

See a live example:
- [Demo task specification](demo/task.txt)
- [Generated patch](demo/patch.diff)
- [Test results](demo/test_results.txt)
- [Example PR](../../pulls?q=label:agent-generated) - PRs labeled `agent-generated`

## Advanced: DSPy Optimization

You can optimize the agent's prompts using DSPy teleprompting:

```python
from dspy.teleprompt import BootstrapFewShotWithRandomSearch

# Collect training examples
examples = [
    dspy.Example(
        task="Add type hints",
        repo_state=repo_snapshot(...),
        allowed_patterns="src/**/*.py",
        patch="<expected-patch>"
    ).with_inputs("task", "repo_state", "allowed_patterns")
]

# Optimize
optimizer = BootstrapFewShotWithRandomSearch(
    metric=lambda example, pred, trace: tests_pass(pred.patch),
    max_bootstrapped_demos=3
)

optimized_agent = optimizer.compile(CodeAgent(), trainset=examples)
```

## Why This Example?

This coding agent demonstrates:

1. **Real-world DSPy usage** - Not just routing, but complex structured generation
2. **End-to-end observability** - Every decision traced in Langfuse
3. **Production guardrails** - File restrictions, risk assessment, automated testing
4. **Verifiable output** - Git commits and PRs provide auditable evidence

Perfect for demonstrating agent capabilities to potential employers or collaborators.

## License

MIT (same as parent project)
