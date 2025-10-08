"""Environment configuration helpers for the AgentOps starter agent."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional
from pathlib import Path

import dspy

try:  # Optional dependency at runtime if Langfuse creds are provided
    from langfuse import Langfuse
except Exception:  # pragma: no cover - langfuse import is optional for tests
    Langfuse = None  # type: ignore

LOGGER = logging.getLogger(__name__)
_LANGFUSE_CLIENT: Optional["Langfuse"] = None


def _load_dotenv_into_env() -> None:
    """Best-effort .env loader without adding a dependency.

    - Looks for a `.env` in CWD and up to three parent directories.
    - Parses simple KEY=VALUE lines, ignoring blanks and comments.
    - Does not override variables that are already set in `os.environ`.
    """

    candidates = []
    try:
        cwd = Path.cwd()
        candidates.append(cwd / ".env")
        for p in list(Path(__file__).resolve().parents)[:4]:
            candidates.append(p / ".env")
    except Exception:
        return

    for env_path in candidates:
        try:
            if not env_path.exists():
                continue
            for raw in env_path.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip()
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            # Never crash on dotenv parsing
            continue


def configure_lm_from_env() -> bool:
    """Configure DSPy to use an LM if `OPENAI_*` environment variables are set.

    Supports both `dspy.settings.configure(...)` and `dspy.configure(...)` APIs,
    and validates that the LM is actually visible after configuration.
    """

    # Load .env if present so local runs (e.g., make targets) pick up keys
    _load_dotenv_into_env()

    # Already configured?
    existing = getattr(dspy.settings, "get", lambda *_: None)("lm")
    if existing is None:
        existing = getattr(dspy.settings, "lm", None)
    if existing is not None:
        return True

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        LOGGER.debug("OPENAI_API_KEY not set; leaving DSPy LM unconfigured")
        return False

    model = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
    lm_kwargs: Dict[str, Any] = {"api_key": api_key}

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        lm_kwargs["base_url"] = base_url

    temperature = os.getenv("OPENAI_TEMPERATURE")
    if temperature:
        try:
            lm_kwargs["temperature"] = float(temperature)
        except ValueError:
            LOGGER.warning("Invalid OPENAI_TEMPERATURE value %s; ignoring", temperature)

    lm = dspy.LM(model, **lm_kwargs)

    # Try modern API first (dspy.settings.configure), then also call legacy
    # dspy.configure for maximum compatibility across DSPy versions.
    configured = False
    try:
        if hasattr(dspy, "settings") and hasattr(dspy.settings, "configure"):
            dspy.settings.configure(lm=lm)
            configured = True
        if hasattr(dspy, "configure"):
            # Some versions rely on this global helper
            dspy.configure(lm=lm)  # type: ignore[misc]
            configured = True
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Failed to configure DSPy LM: %s", exc)
        configured = False

    # Validate visibility via both access patterns
    check = getattr(dspy.settings, "get", lambda *_: None)("lm")
    if check is None:
        check = getattr(dspy.settings, "lm", None)

    if configured and check is not None:
        LOGGER.info("Configured DSPy LM with model %s", model)
        return True

    LOGGER.warning("DSPy LM configuration attempted but not visible in settings; falling back")
    return False


def configure_langfuse_from_env() -> Optional["Langfuse"]:
    """Initialise a Langfuse client if credentials are present."""

    global _LANGFUSE_CLIENT

    if Langfuse is None:
        LOGGER.debug("langfuse package not available; skipping Langfuse setup")
        return None

    if _LANGFUSE_CLIENT is not None:
        return _LANGFUSE_CLIENT

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not (public_key and secret_key):
        LOGGER.debug("LANGFUSE credentials not set; skipping Langfuse setup")
        return None

    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    try:
        _LANGFUSE_CLIENT = Langfuse(  # type: ignore[call-arg]
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
    except Exception as exc:  # pragma: no cover - protective against runtime failures
        LOGGER.warning("Failed to configure Langfuse: %s", exc)
        _LANGFUSE_CLIENT = None
    else:
        LOGGER.info("Configured Langfuse client targeting %s", host)

    return _LANGFUSE_CLIENT


def log_langfuse_generation(
    *,
    name: str,
    input_text: str,
    output_payload: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Send a simple generation observation to Langfuse, if configured."""

    client = configure_langfuse_from_env()
    if client is None:
        return

    try:
        model = getattr(getattr(dspy.settings, "lm", None), "model", None)
        observation = client.start_observation(
            name=name,
            as_type="generation",
            input={"ticket": input_text},
            output=output_payload,
            metadata=metadata,
            model=model,
        )
        observation.update(output=output_payload)
        observation.end()
        client.flush()
    except Exception as exc:  # pragma: no cover - tracing should never crash the agent
        LOGGER.debug("Langfuse logging failed: %s", exc, exc_info=True)


__all__ = [
    "configure_lm_from_env",
    "configure_langfuse_from_env",
    "log_langfuse_generation",
]
