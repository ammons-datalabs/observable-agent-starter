"""Tests for BaseAgent."""

import pytest
import dspy
from observable_agent_starter import BaseAgent, config


@pytest.fixture(autouse=True)
def reset_dspy():
    """Reset DSPy settings before each test."""
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]
    yield
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]


def test_base_agent_initialization():
    """BaseAgent should initialize with observation name."""
    agent = BaseAgent(observation_name="test-agent")

    assert agent.observation_name == "test-agent"
    assert agent.logger.name.endswith("test-agent")


def test_base_agent_auto_configures_lm(monkeypatch):
    """BaseAgent should auto-configure LM from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai/test-model")

    BaseAgent(observation_name="test-agent")

    lm = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
    if lm is None:
        lm = getattr(dspy.settings, "lm", None)
    assert lm is not None


def test_base_agent_handles_missing_lm(monkeypatch):
    """BaseAgent should handle missing LM gracefully."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "_load_dotenv_into_env", lambda: None)

    # Should not raise
    agent = BaseAgent(observation_name="test-agent")

    assert agent.observation_name == "test-agent"


def test_log_generation_helper(monkeypatch):
    """BaseAgent.log_generation should call log_langfuse_generation."""
    import observable_agent_starter.base_agent as base_agent_module

    calls = []

    def mock_log(*, name, input_text, output_payload, metadata=None):
        calls.append({
            "name": name,
            "input_text": input_text,
            "output_payload": output_payload,
            "metadata": metadata
        })

    monkeypatch.setattr(base_agent_module, "log_langfuse_generation", mock_log)

    agent = BaseAgent(observation_name="test-agent")
    agent.log_generation(
        input_data={"test": "input"},
        output_data={"result": "output"},
        custom_meta="value"
    )

    assert len(calls) == 1
    assert calls[0]["name"] == "test-agent"
    assert "test" in calls[0]["input_text"]
    assert calls[0]["output_payload"] == {"result": "output"}
    assert calls[0]["metadata"]["custom_meta"] == "value"
