"""Unit tests for the Observable Agent Starter routing agent."""

from __future__ import annotations

from typing import Any

import dspy
import pytest

from observable_agent_starter.agents.routing import StarterAgent, ExampleAgent, ALLOWED_ROUTES
from observable_agent_starter.agents.routing import config


class DummyPrediction:
    def __init__(self, route: str, explanation: str = "") -> None:
        self.route = route
        self.rationale = explanation


class DummyPredictor:
    def __init__(self, route: str) -> None:
        self._route = route

    def __call__(self, **_: Any) -> DummyPrediction:  # pragma: no cover - trivial
        return DummyPrediction(self._route)


@pytest.fixture(autouse=True, scope="function")
def reset_dspy_settings():
    """Reset DSPy settings before each test in this module only."""
    import dspy.dsp.utils.settings as dspy_settings_module

    # Reset the thread ownership so each test can configure
    dspy_settings_module.config_owner_thread_id = None
    dspy_settings_module.config_owner_async_task = None

    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]
    yield

    # Reset again after test
    dspy_settings_module.config_owner_thread_id = None
    dspy_settings_module.config_owner_async_task = None
    dspy.settings.configure(lm=None)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]


def test_policy_fallback_triggers_on_invalid_route():
    agent = ExampleAgent()
    agent.route = DummyPredictor("escalate")  # type: ignore[assignment]

    result = agent.forward("Need pricing clarification")

    assert result["route"] in ALLOWED_ROUTES
    assert "fallback" in result["explanation"].lower()


def test_configure_lm_from_env_sets_dspy_lm(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "openai/test")

    configured = config.configure_lm_from_env()

    assert configured is True
    lm = dspy.settings.get("lm")
    assert lm is not None
    assert getattr(lm, "model", None) == "openai/test"


def test_configure_langfuse_from_env_skips_without_creds(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]
    client = config.configure_langfuse_from_env()
    assert client is None


def test_configure_langfuse_from_env_initialises_client(monkeypatch):
    class FakeLangfuse:  # pragma: no cover - behaviour is exercised through config
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def trace(self, **kwargs: Any) -> "FakeTrace":  # pragma: no cover
            return FakeTrace()

    class FakeTrace:  # pragma: no cover - used to satisfy log function if invoked
        def generation(self, **_: Any) -> None:
            return None

        def flush(self) -> None:
            return None

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://example")
    monkeypatch.setattr(config, "Langfuse", FakeLangfuse)
    config._LANGFUSE_CLIENT = None  # type: ignore[attr-defined]

    client = config.configure_langfuse_from_env()

    assert isinstance(client, FakeLangfuse)
    assert client.kwargs["public_key"] == "pk-test"
    # second call should reuse cached client
    assert config.configure_langfuse_from_env() is client


def test_log_langfuse_generation_handles_absent_client(monkeypatch):
    monkeypatch.setattr(config, "configure_langfuse_from_env", lambda: None)

    # Should no-op without raising
    config.log_langfuse_generation(
        name="test",
        input_text="hello",
        output_payload={"route": "tech"},
    )


def test_log_langfuse_generation_emits_observation(monkeypatch):
    calls = {}

    class FakeObservation:
        def update(self, **kwargs: Any) -> None:  # pragma: no cover - trivial
            calls.setdefault("update", []).append(kwargs)

        def end(self, **kwargs: Any) -> None:  # pragma: no cover - trivial
            calls.setdefault("end", []).append(kwargs)

    class FakeClient:
        def start_observation(self, **kwargs: Any):  # pragma: no cover - trivial
            calls.setdefault("start_observation", []).append(kwargs)
            return FakeObservation()

        def flush(self) -> None:  # pragma: no cover - trivial
            calls.setdefault("flush", []).append(True)

    monkeypatch.setattr(config, "configure_langfuse_from_env", lambda: FakeClient())

    config.log_langfuse_generation(
        name="test",
        input_text="hello",
        output_payload={"route": "tech"},
        metadata={"foo": "bar"},
    )

    assert "start_observation" in calls
    obs_kwargs = calls["start_observation"][0]
    assert obs_kwargs["name"] == "test"
    assert obs_kwargs["as_type"] == "generation"
    assert obs_kwargs["input"]["ticket"] == "hello"
    assert calls.get("flush")
