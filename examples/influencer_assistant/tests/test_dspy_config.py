from __future__ import annotations


import dspy
import pytest

from influencer_assistant.dspy.config import configure_lm_from_env, reset_lm


@pytest.fixture(autouse=True)
def cleanup_lm():
    reset_lm()
    yield
    reset_lm()


def test_configure_lm_from_env_without_key_returns_false(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Also patch the _load_dotenv_into_env function to prevent .env file loading
    monkeypatch.setattr("agents.example.config._load_dotenv_into_env", lambda: None)
    assert configure_lm_from_env() is False
    assert dspy.settings.get("lm") is None


def test_configure_lm_from_env_with_key(monkeypatch):
    class FakeLM:  # minimal stub to avoid network calls
        def __init__(self, model: str, **kwargs):
            self.model = model
            self.kwargs = kwargs

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai/test-model")
    monkeypatch.setattr("influencer_assistant.dspy.config.dspy.LM", FakeLM)

    configured = configure_lm_from_env()

    assert configured is True
    lm = dspy.settings.get("lm")
    assert isinstance(lm, FakeLM)
    assert lm.model == "openai/test-model"
    assert lm.kwargs["api_key"] == "test-key"

    # Ensure repeat calls are harmless
    assert configure_lm_from_env() is True
