"""Observable Agent Starter - DSPy agent framework with observability."""

__version__ = "0.3.0"

from .observability import ObservabilityProvider, create_observability
from .config import configure_lm_from_env, log_langfuse_generation

__all__ = [
    "ObservabilityProvider",
    "create_observability",
    "configure_lm_from_env",
    "log_langfuse_generation",
]
