# Influencer Assistant Example

This example demonstrates extending `observable_agent_starter.BaseAgent` for content ideation with DeepEval quality metrics.

## Extending BaseAgent

```python
from observable_agent_starter import BaseAgent
import dspy

class VideoIdeaGenerator(dspy.Module, BaseAgent):
    """Generate video ideas extending BaseAgent."""

    def __init__(self):
        dspy.Module.__init__(self)
        BaseAgent.__init__(self, observation_name="influencer-video-ideas")

        # Your agent setup
        self.predict = dspy.Predict(VideoIdeaSignature)
```

**What BaseAgent provides:**
- LM configuration from environment variables
- Langfuse tracing helpers (`self.log_generation()`)
- Logging infrastructure

**What this example adds:**
- DSPy signatures for idea generation
- Profile context rendering
- Fallback logic for missing LM
- **DeepEval quality metrics** (relevancy, faithfulness, pillar adherence)

## What's Included

This example demonstrates how to combine DSPy reasoning and structured data modeling
to support an AI assistant that helps manage creator operations. It includes:

- `InfluencerProfile` and `InfluencerProfileBuilder` for normalizing creator inputs
- Prompt context and video idea generation modules built with DSPy
- Synthetic fixtures that mimic real creator portfolios
- Pytest suites covering the builder, DSPy configuration, and content generator

## Installation

Install with development dependencies:

```bash
cd examples/influencer_assistant
pip install -e '.[dev]'
```

## Testing

Run unit tests:
```bash
pytest tests/ -v
```

## DeepEval Quality Metrics

This example showcases LLM evaluation with DeepEval:

- **Relevancy**: Ideas match user request
- **Faithfulness**: Ideas grounded in creator profile
- **Pillar adherence**: Ideas map to content pillars

Run quality metrics:
```bash
export OPENAI_API_KEY=your-key
pytest evals/ -v
```

These metrics run in CI and must pass.

## Dashboard
Run the optional Streamlit dashboard to explore the portfolio data and generate ideas:

```bash
.venv/bin/pip install -e '.[examples]'  # If not already installed
make demo-influencer
```

The app loads the synthetic creator snapshots, visualises key metrics, and lets you
invoke the DSPy-powered video idea generator through an interactive form.

When `LANGFUSE_*` environment variables are present, generated ideas are traced to the
same Langfuse project used by the core Observable Agent Starter (observation name
`influencer-video-ideas`).

## Prompt tuning
Run DSPy's teleprompting utilities to refine the idea generator instructions:

```bash
.venv/bin/pip install -e '.[examples]'  # If not already installed
make tune-influencer ARGS="--num-candidates 6"
```

The script optimises the prompt using the synthetic training set and writes the tuned
instructions to `examples/influencer_assistant/prompts/video_ideas_optimized.txt` for you
to review or wire into the generator.
