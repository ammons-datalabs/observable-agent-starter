"""Tests for config module."""

import pytest
import dspy
from observable_agent_starter import config


@pytest.fixture(autouse=True)
def reset_dspy():
    """Reset DSPy settings before each test."""
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]
    yield
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]


def test_configure_lm_from_env_without_key(monkeypatch):
    """Should return False when no API key is set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(config, "_load_dotenv_into_env", lambda: None)

    result = config.configure_lm_from_env()

    assert result is False
    lm = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
    if lm is None:
        lm = getattr(dspy.settings, "lm", None)
    assert lm is None


def test_configure_lm_from_env_with_key(monkeypatch):
    """Should configure LM when API key is set."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai/test-model")

    result = config.configure_lm_from_env()

    assert result is True
    lm = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
    if lm is None:
        lm = getattr(dspy.settings, "lm", None)
    assert lm is not None


def test_configure_lm_from_env_is_idempotent(monkeypatch):
    """Should not reconfigure if already configured."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result1 = config.configure_lm_from_env()
    result2 = config.configure_lm_from_env()

    assert result1 is True
    assert result2 is True


def test_configure_langfuse_without_creds(monkeypatch):
    """Should return None when credentials are missing."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    client = config.configure_langfuse_from_env()

    assert client is None


def test_log_langfuse_generation_handles_no_client(monkeypatch):
    """Should not crash when Langfuse client is unavailable."""
    monkeypatch.setattr(config, "configure_langfuse_from_env", lambda: None)

    # Should not raise
    config.log_langfuse_generation(
        name="test",
        input_text="test input",
        output_payload={"result": "test"}
    )
