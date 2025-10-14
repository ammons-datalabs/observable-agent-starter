# Observable Agent Starter

[![Tests](https://github.com/ammons-datalabs/observable-agent-starter/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ammons-datalabs/observable-agent-starter/actions/workflows/ci.yml)

Production-ready Python agent starter with built-in observability, evaluation, and CI.  
Pre-wired with:

- **DSPy** (or LangGraph) for agent logic  
- **Langfuse** for tracing and observability  
- **DeepEval** for LLM quality metrics  
- **FastAPI** for production-ready HTTP endpoints  
- **MCP client adapters** for tool-calling across MCP servers  
- **GitHub Actions CI** for linting, type-checking, tests, and evals  

---

## Why It’s Useful for SMEs

Small engineering teams need agents that work reliably from day one.  
This starter eliminates weeks of integration work by pre-wiring **DSPy**, **Langfuse**, **DeepEval**, **FastAPI**, and **GitHub Actions CI**.

You get a **debuggable, testable agent architecture with observability baked in** — so you can focus on your domain logic instead of infrastructure.  
The included thin-triage example shows the pattern; swap in your own tools and prompts and ship confidently.

---

## Demo

### CLI Agent

```bash
# Run the example agent directly
python -m agents.example
# {"route": "billing", "explanation": "Policy fallback used..."}
```

### FastAPI Server

```bash
# Start the server
uvicorn examples.fastapi_server:app --reload

# Test the /route endpoint
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"request": "My invoice has extra charges"}'

# Response: {"route": "billing", "explanation": "..."}
```

---

## Quick Start

```bash
# 1) Create venv & install deps (installs into .venv by default)
make dev

# 2) (Optional) export model + Langfuse creds
export OPENAI_API_KEY=...
export OPENAI_MODEL=openai/gpt-4o-mini  # optional override
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
export LANGFUSE_HOST=https://cloud.langfuse.com

# 3) Run the CLI agent
make run

# 4) Run tests + evals
make test
```

> Targets look for the virtual environment at `.venv` by default.  
> To use an existing environment (for example managed by `pyenv`), override the path when invoking `make`, e.g.  
> `make VENV=$(pyenv prefix) test`.

Use `make evals` for DeepEval CLI guidance once you have credentials configured.

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

## Structure

```
.
├─ agents/example/         # Example agent (DSPy-based routing)
│  ├─ agent.py             # ExampleAgent (swap with your logic)
│  ├─ config.py            # LM + Langfuse setup
│  └─ policy.py            # Fallback routing policy
├─ examples/
│  ├─ fastapi_server.py    # FastAPI production server
│  └─ influencer_assistant/  # Richer DSPy example
├─ tests/                  # Unit tests (24 passing)
├─ evals/deepeval/         # DeepEval quality metrics
├─ prompts/                # Jinja2 prompt templates
├─ mcp/servers.json        # MCP server configs
├─ .github/workflows/ci.yml  # CI pipeline
├─ pyproject.toml
├─ Makefile
└─ README.md
```

---

## Notes

- **Swap the example agent** with your own logic — all main logic lives in `agents/example/agent.py` (`ExampleAgent` class).  
- Switch between **DSPy** and **LangGraph** easily; framework logic is isolated.  
- `mcp/servers.json` defines Langfuse MCP servers or your own custom ones.  
- Keep prompts in `prompts/` or use managed prompts via MCP.  
- The example agent auto-configures DSPy from `OPENAI_*` env vars, falls back to a routing policy if the LM misbehaves, and logs all interactions to Langfuse when credentials exist.  
- The **FastAPI server** (`examples/fastapi_server.py`) provides production-ready endpoints with automatic tracing.

---

## Examples

- `examples/influencer_assistant/` includes a richer DSPy example modelling a creator portfolio that generates content ideas and comes with pytest coverage.
  Install its dependencies with:
  ```bash
  make dev  # First ensure .venv exists
  .venv/bin/pip install -e '.[examples]'
  ```
  Then run:
  ```bash
  make test-examples
  ```
  Launch the optional Streamlit dashboard:
  ```bash
  make demo-influencer
  ```
  Idea runs are traced to Langfuse (`observation: influencer-video-ideas`) when `LANGFUSE_*` environment variables are set.  
  You can experiment with DSPy teleprompting via:
  ```bash
  make tune-influencer ARGS="--num-candidates 4"
  ```
  (requires LM credentials) to generate a refined prompt saved under  
  `examples/influencer_assistant/prompts/`.

---

## License

MIT

---

> **Ammons Data Labs** builds observable, measurable AI agents and data systems — from fast prototypes to hardened services.
