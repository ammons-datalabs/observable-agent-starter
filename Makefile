# Simple dev workflow
.PHONY: dev lint type test coverage precommit evals test-examples demo-influencer tune-influencer run

VENV ?= .venv
PYTHON_BOOTSTRAP ?= python3
PYTHON := $(VENV)/bin/python
UV := $(VENV)/bin/uv

dev:
	$(PYTHON_BOOTSTRAP) -m venv $(VENV)
	$(PYTHON) -m pip install -U pip uv
	$(UV) pip install -e '.[dev]'
	@echo "✅ Development environment ready!"
	@echo "📝 Next steps:"
	@echo "   - Run 'make precommit' to install git hooks"
	@echo "   - Run 'make test' to verify setup"

lint:
	$(VENV)/bin/ruff check .

type:
	$(VENV)/bin/pyright

test:
	$(PYTHON) -m pytest -v

coverage:
	$(PYTHON) -m pytest --cov=observable_agent_starter --cov-report=html --cov-report=term-missing
	@echo "📊 Coverage report generated in htmlcov/index.html"

precommit:
	$(VENV)/bin/pre-commit install
	$(VENV)/bin/pre-commit run --all-files

test-examples:
	@if ! $(PYTHON) -c "import pydantic" >/dev/null 2>&1; then \
		echo "Install example extras first: pip install -e '.[examples]'"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest examples/influencer_assistant/tests -q

evals:
	@if [ ! -x "$(VENV)/bin/deepeval" ]; then \
		echo "DeepEval CLI not installed in $(VENV). Run 'make dev' first."; \
		exit 1; \
	fi
	$(PYTHON) -m pytest evals/deepeval/ -v

demo-influencer:
	@if [ ! -x "$(VENV)/bin/streamlit" ]; then \
		echo "Install example extras first: pip install -e '.[examples]'"; \
		exit 1; \
	fi
	$(VENV)/bin/streamlit run examples/influencer_assistant/dashboard/app.py

tune-influencer:
	@if ! $(PYTHON) -c "import dspy" >/dev/null 2>&1; then \
		echo "Install example extras first: pip install -e '.[examples]'"; \
		exit 1; \
	fi
	$(PYTHON) examples/influencer_assistant/training/tune_video_ideas.py $(ARGS)

run:
	$(PYTHON) -m observable_agent_starter.agents.routing

server:
	$(VENV)/bin/uvicorn observable_agent_starter.servers.api:app --reload
