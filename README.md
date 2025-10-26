# Observable Agent Starter

[![Tests](https://github.com/ammons-datalabs/observable-agent-starter/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ammons-datalabs/observable-agent-starter/actions/workflows/ci.yml)

**Production-ready DSPy agent framework with Langfuse observability, automated testing, and deployment templates.**

## What This Starter Gives You

| Component | What | Where |
|-----------|------|-------|
| **Base Framework** | Thin `BaseAgent` with config + tracing | `src/observable_agent_starter/` |
| **Observability** | Langfuse integration | Auto-configured via env vars |
| **Testing** | pytest + CI/CD | `tests/` + GitHub Actions |
| **Examples** | Coding agent + Influencer assistant | `examples/` |
| **Evaluations** | DeepEval (example-scoped) | `examples/influencer_assistant/evals/` |

## Pre-wired Stack

- **DSPy** - Structured LLM programming
- **Langfuse** - Observability and tracing
- **pytest** - Testing framework
- **DeepEval** - LLM quality metrics (influencer example)
- **GitHub Actions** - CI/CD pipeline

---

## Quick Start

```bash
# 1. Install
make dev

# 2. Configure
export OPENAI_API_KEY=...
export LANGFUSE_PUBLIC_KEY=...      # Optional
export LANGFUSE_SECRET_KEY=...      # Optional

# 3. Run tests
make test
```

---

## Structure

```
src/observable_agent_starter/   # Core framework
  ├── base_agent.py              # Thin base with config + tracing
  ├── config.py                  # LM + Langfuse configuration
  └── __init__.py

examples/                        # Example implementations
  ├── coding_agent/              # Code generation with gates
  └── influencer_assistant/      # Content ideation with DeepEval

tests/                           # Framework tests
  ├── test_base_agent.py
  └── test_config.py
```

---

## Examples

### 1. Coding Agent - Agent-in-the-Loop

Demonstrates:
- Extending `BaseAgent` for code generation
- DSPy Chain-of-Thought with guardrails
- Git integration + PR workflow
- Operational quality gates (lint, tests, type-check)

**Try the demo:**
```bash
cd examples/coding_agent
pip install -e .

# Run on the included sample project
adl-agent "Add a multiply function with docstring" \
  --repo demo/sample_project \
  --allow "*.py"

# Or use on your own repo
adl-agent "Add docstrings to public functions" \
  --repo /path/to/your/repo \
  --allow "src/**/*.py"
```

[Full documentation →](examples/coding_agent/README.md)

### 2. Influencer Assistant - DeepEval Showcase

Demonstrates:
- Extending `BaseAgent` for content ideation
- DSPy prompt optimization (teleprompting)
- **DeepEval quality metrics** (relevancy, faithfulness, pillar adherence)
- Streamlit dashboard

```bash
cd examples/influencer_assistant
pip install -e '.[dev]'

# Run tests + evals
pytest tests/ -v
pytest evals/ -v

# Launch dashboard
streamlit run dashboard/app.py
```

[Full documentation →](examples/influencer_assistant/README.md)

---

## Extending BaseAgent

```python
from observable_agent_starter import BaseAgent
import dspy

class MyAgent(dspy.Module, BaseAgent):
    """Your custom agent."""

    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="my-agent")

        # Your DSPy signatures, modules, etc.
        self.predict = dspy.ChainOfThought(MySignature)

    def forward(self, **kwargs):
        # Your agent logic
        result = self.predict(**kwargs)

        # Log to Langfuse
        self.log_generation(
            input_data=kwargs,
            output_data={"result": result.output}
        )

        return result
```

**BaseAgent provides:**
- Automatic LM configuration from `OPENAI_*` env vars
- Langfuse tracing helper (`self.log_generation()`)
- Logging infrastructure

**You provide:**
- DSPy signatures and modules
- Agent logic and fallback handling
- Domain-specific evaluation strategy

---

## Why This Helps

**For Production:**
- Observable by default (Langfuse traces)
- Testable (pytest + CI)
- Deployable (FastAPI patterns in examples)

**For Synthenova/Employer Showcase:**
- ✅ Agent-in-the-loop pattern (coding agent)
- ✅ Eval discipline (influencer DeepEval)
- ✅ Observability-first design (Langfuse)

---

## Using with GitHub or Codespaces

1. Create a new empty repo on GitHub (public for open source).
2. Download this starter as a ZIP, unzip, then:
   ```bash
   git init
   git add .
   git commit -m "chore: bootstrap Observable Agent Starter"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
3. Open in Codespaces (or clone locally). CI will run automatically on each PR.
4. Add `LANGFUSE_*` keys as repo or Codespaces secrets if you want tracing enabled.

---

## License

MIT

---

> **Ammons Data Labs** builds observable, measurable AI agents and data systems.
