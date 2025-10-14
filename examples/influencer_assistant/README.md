# Influencer Assistant Example

This example demonstrates how to combine DSPy reasoning and structured data modeling
to support an AI assistant that helps manage creator operations. It includes:

- `InfluencerProfile` and `InfluencerProfileBuilder` for normalizing creator inputs
- Prompt context and video idea generation modules built with DSPy
- Synthetic fixtures that mimic real creator portfolios
- Pytest suites covering the builder, DSPy configuration, and content generator

The example is designed to live under `examples/influencer_assistant/` within the
Observable Agent Starter repository. Install the extra dependencies and run its tests with:

```bash
make dev
pip install -e '.[examples]'
make test-examples
```

## Dashboard
Run the optional Streamlit dashboard to explore the portfolio data and generate ideas:

```bash
pip install -e '.[examples]'
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
pip install -e '.[examples]'
make tune-influencer ARGS="--num-candidates 6"
```

The script optimises the prompt using the synthetic training set and writes the tuned
instructions to `examples/influencer_assistant/prompts/video_ideas_optimized.txt` for you
to review or wire into the generator.
