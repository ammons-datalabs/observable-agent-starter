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


def test_load_dotenv_with_valid_env_file(tmp_path, monkeypatch):
    """Should load valid .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_KEY=test_value\nANOTHER_KEY=another_value")

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TEST_KEY", raising=False)

    config._load_dotenv_into_env()

    assert "TEST_KEY" in config.os.environ
    assert config.os.environ["TEST_KEY"] == "test_value"


def test_load_dotenv_with_comments_and_blanks(tmp_path, monkeypatch):
    """Should ignore comments and blank lines in .env."""
    env_file = tmp_path / ".env"
    env_file.write_text("""
# This is a comment
TEST_KEY=test_value

# Another comment
ANOTHER_KEY=another_value
    """)

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TEST_KEY", raising=False)

    config._load_dotenv_into_env()

    assert config.os.environ.get("TEST_KEY") == "test_value"


def test_load_dotenv_with_invalid_lines(tmp_path, monkeypatch):
    """Should skip lines without = sign."""
    env_file = tmp_path / ".env"
    env_file.write_text("""
VALID_KEY=valid_value
INVALID_LINE_WITHOUT_EQUALS
ANOTHER_VALID=another_value
    """)

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VALID_KEY", raising=False)

    config._load_dotenv_into_env()

    assert config.os.environ.get("VALID_KEY") == "valid_value"
    assert config.os.environ.get("ANOTHER_VALID") == "another_value"


def test_load_dotenv_doesnt_override_existing_env(tmp_path, monkeypatch):
    """Should not override existing environment variables."""
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING_KEY=new_value")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EXISTING_KEY", "existing_value")

    config._load_dotenv_into_env()

    assert config.os.environ["EXISTING_KEY"] == "existing_value"


def test_load_dotenv_handles_nonexistent_file(tmp_path, monkeypatch):
    """Should handle missing .env file gracefully."""
    monkeypatch.chdir(tmp_path)

    # Should not raise
    config._load_dotenv_into_env()


def test_configure_lm_with_base_url(monkeypatch):
    """Should configure LM with custom base URL."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.openai.com")

    result = config.configure_lm_from_env()

    assert result is True


def test_configure_lm_with_valid_temperature(monkeypatch):
    """Should configure LM with valid temperature."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "0.7")

    result = config.configure_lm_from_env()

    assert result is True


def test_configure_lm_with_invalid_temperature(monkeypatch):
    """Should ignore invalid temperature value."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "not-a-number")

    result = config.configure_lm_from_env()

    assert result is True  # Should still configure, just ignore temperature


def test_configure_langfuse_with_custom_host(monkeypatch):
    """Should configure Langfuse with custom host."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret")
    monkeypatch.setenv("LANGFUSE_HOST", "https://custom.langfuse.com")

    # Mock Langfuse to avoid actual connection
    class MockLangfuse:
        def __init__(self, public_key, secret_key, host):
            self.public_key = public_key
            self.secret_key = secret_key
            self.host = host

    monkeypatch.setattr(config, "Langfuse", MockLangfuse)

    client = config.configure_langfuse_from_env()

    assert client is not None
    assert client.host == "https://custom.langfuse.com"


def test_configure_langfuse_uses_default_host(monkeypatch):
    """Should use default Langfuse host when not specified."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret")
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)

    class MockLangfuse:
        def __init__(self, public_key, secret_key, host):
            self.host = host

    monkeypatch.setattr(config, "Langfuse", MockLangfuse)

    client = config.configure_langfuse_from_env()

    assert client is not None
    assert client.host == "https://cloud.langfuse.com"


def test_configure_langfuse_is_singleton(monkeypatch):
    """Should return the same Langfuse client on repeated calls."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret")

    class MockLangfuse:
        def __init__(self, public_key, secret_key, host):
            pass

    monkeypatch.setattr(config, "Langfuse", MockLangfuse)

    client1 = config.configure_langfuse_from_env()
    client2 = config.configure_langfuse_from_env()

    assert client1 is client2


def test_log_langfuse_generation_with_metadata(monkeypatch):
    """Should log generation with metadata to Langfuse."""
    class MockObservation:
        def __init__(self):
            self.output = None

        def update(self, output):
            self.output = output

        def end(self):
            pass

    class MockLangfuse:
        def __init__(self, public_key, secret_key, host):
            self.observations = []

        def start_observation(self, name, as_type, input, output, metadata, model):
            obs = MockObservation()
            self.observations.append({
                "name": name,
                "type": as_type,
                "input": input,
                "output": output,
                "metadata": metadata,
                "model": model
            })
            return obs

        def flush(self):
            pass

    mock_client = MockLangfuse("pk", "sk", "https://test.com")
    monkeypatch.setattr(config, "configure_langfuse_from_env", lambda: mock_client)

    # Configure DSPy with a mock LM that has a model attribute
    class MockLM:
        model = "test-model"

    dspy.settings.configure(lm=MockLM())

    config.log_langfuse_generation(
        name="test-generation",
        input_text="test input",
        output_payload={"result": "test output"},
        metadata={"key": "value"}
    )

    assert len(mock_client.observations) == 1
    obs = mock_client.observations[0]
    assert obs["name"] == "test-generation"
    assert obs["metadata"] == {"key": "value"}
