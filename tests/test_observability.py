"""Tests for ObservabilityProvider."""

import pytest
import dspy
from observable_agent_starter import ObservabilityProvider, create_observability, config


@pytest.fixture(autouse=True)
def reset_dspy():
    """Reset DSPy settings before each test."""
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]
    yield
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]


def test_observability_provider_initialization():
    """ObservabilityProvider should initialize with observation name."""
    provider = ObservabilityProvider(observation_name="test-agent")

    assert provider.observation_name == "test-agent"
    assert provider.logger.name.endswith("test-agent")


def test_create_observability_auto_configures_lm(monkeypatch):
    """create_observability should auto-configure LM from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai/test-model")

    provider = create_observability("test-agent")

    assert provider.observation_name == "test-agent"
    lm = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
    if lm is None:
        lm = getattr(dspy.settings, "lm", None)
    assert lm is not None


def test_create_observability_without_lm_configuration(monkeypatch):
    """create_observability with configure_lm=False should not configure LM."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai/test-model")

    provider = create_observability("test-agent", configure_lm=False)

    assert provider.observation_name == "test-agent"
    lm = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
    if lm is None:
        lm = getattr(dspy.settings, "lm", None)
    assert lm is None


def test_create_observability_handles_missing_lm(monkeypatch):
    """create_observability should handle missing LM gracefully."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "_load_dotenv_into_env", lambda: None)

    # Should not raise
    provider = create_observability("test-agent")

    assert provider.observation_name == "test-agent"


def test_log_generation_helper(monkeypatch):
    """ObservabilityProvider.log_generation should call log_langfuse_generation."""
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

    provider = ObservabilityProvider(observation_name="test-agent")
    provider.log_generation(
        input_data={"test": "input"},
        output_data={"result": "output"},
        custom_meta="value"
    )

    assert len(calls) == 1
    assert calls[0]["name"] == "test-agent"
    assert "test" in calls[0]["input_text"]
    assert calls[0]["output_payload"] == {"result": "output"}
    assert calls[0]["metadata"]["custom_meta"] == "value"


def test_observability_provider_composition_pattern():
    """ObservabilityProvider should work with composition pattern."""
    import dspy

    class TestAgent(dspy.Module):
        def __init__(self, observability: ObservabilityProvider):
            super().__init__()
            self.observability = observability

        def forward(self, input_text: str):
            return f"processed: {input_text}"

    provider = ObservabilityProvider("test-composition")
    agent = TestAgent(observability=provider)

    assert agent.observability.observation_name == "test-composition"
    result = agent(input_text="hello")
    assert result == "processed: hello"