# Influencer Assistant Example

An AI-powered content ideation assistant that helps creators generate video ideas based on their profile, audience, and content pillars.

## Overview

This example demonstrates a **production-ready approach** to building domain-specific AI assistants with measurable quality. Unlike generic chatbots, this assistant:

- Uses structured creator profiles (audience, content pillars, past performance)
- Generates ideas grounded in real creator data
- Validates output quality with automated LLM evaluations (DeepEval)
- Provides full observability via Langfuse tracing

This pattern is ideal for any application where AI needs to generate content that's both creative and constrained by business context.

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

This example showcases **LLM-as-a-judge evaluation** with DeepEval. Instead of relying on manual review, we use automated metrics to validate output quality:

### Metrics Explained

1. **Relevancy** - Do the generated ideas actually match what the user requested?
   - Uses semantic similarity between request and output
   - Threshold: 0.7 (70% relevant content required)
   - Example: If user asks for "tech tutorials", ideas should be about tech, not cooking

2. **Faithfulness** - Are the ideas grounded in the creator's actual profile?
   - Checks if ideas reference real profile data (audience, pillars, past topics)
   - Threshold: 0.6 (60% of claims must be supported by profile)
   - Prevents hallucination - ideas must use actual creator context

3. **Pillar Adherence** (Custom Metric) - Do ideas map to the creator's content pillars?
   - Custom evaluator that checks if ideas align with declared content themes
   - Example: If pillars are ["Python", "AI", "Career"], ideas should fit these categories
   - Ensures brand consistency

### Running Evaluations

Run quality metrics:
```bash
export OPENAI_API_KEY=your-key
pytest evals/ -v
```

Example output:
```
evals/test_agentops.py::test_video_idea_quality PASSED
  ✓ Relevancy: 0.85 (threshold: 0.7)
  ✓ Faithfulness: 0.72 (threshold: 0.6)
  ✓ Pillar Adherence: PASSED
```

These metrics run in CI and must pass before merging. This ensures the assistant maintains quality even as prompts evolve.

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

## Prompt Tuning

Run DSPy's teleprompting utilities to refine the idea generator instructions:

```bash
.venv/bin/pip install -e '.[examples]'  # If not already installed
make tune-influencer ARGS="--num-candidates 6"
```

The script optimizes the prompt using the synthetic training set and writes the tuned
instructions to `examples/influencer_assistant/prompts/video_ideas_optimized.txt` for you
to review or wire into the generator.

This demonstrates **prompt optimization** - letting DSPy automatically improve prompts based on validation metrics, rather than manual trial-and-error.

---

## Why This Example?

This influencer assistant demonstrates key production patterns:

### 1. Structured Data + LLM Reasoning
Rather than throwing raw text at an LLM, we:
- Model the domain with `InfluencerProfile` (audience, pillars, metrics)
- Use `ProfileBuilder` to normalize messy inputs
- Pass structured context to DSPy modules
- Get more consistent, grounded outputs

### 2. Measurable Quality (LLM-as-a-Judge)
Instead of "vibes-based" evaluation:
- **Automated metrics** validate every output (DeepEval)
- **Thresholds** define acceptable quality
- **CI integration** prevents quality regression
- **Traceable** - see metric scores in Langfuse

### 3. Observable Agent Behavior
Every idea generation is traced:
- Input: creator profile, request
- Process: DSPy reasoning steps
- Output: ideas + quality scores
- Full lineage in Langfuse dashboard

### 4. Production-Ready Patterns
This isn't a toy example:
- Structured fixtures mimic real production data
- Comprehensive test coverage (unit + eval)
- Prompt optimization with DSPy teleprompting
- Interactive dashboard for stakeholder demos

### Use Cases Beyond Influencers

This pattern works for any domain where AI needs to:
- Generate content constrained by business rules
- Use structured context (customer profiles, product catalogs)
- Maintain measurable quality over time
- Provide transparency into AI decisions

Examples:
- **Sales assistants** - Generate emails grounded in CRM data
- **Legal drafting** - Create documents based on case facts
- **Product recommendations** - Suggest items based on user history
- **Medical notes** - Generate summaries from patient records

The key: **Structure + Reasoning + Measurement + Observability**

---

## License

MIT (same as parent project)
