"""Routing agent module - the starter template for your agent."""

from .agent import StarterAgent, ExampleAgent, ALLOWED_ROUTES
from .config import (
    configure_langfuse_from_env,
    configure_lm_from_env,
    log_langfuse_generation,
)
from .policy import neutral_policy

__all__ = [
    "StarterAgent",
    "ExampleAgent",  # Backward compatibility
    "ALLOWED_ROUTES",
    "neutral_policy",
    "configure_lm_from_env",
    "configure_langfuse_from_env",
    "log_langfuse_generation",
]
