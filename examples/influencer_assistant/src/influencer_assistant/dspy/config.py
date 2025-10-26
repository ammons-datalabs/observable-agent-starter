"""Config helpers - delegates to observable_agent_starter."""

from observable_agent_starter import configure_lm_from_env
import dspy


def reset_lm() -> None:
    """Reset DSPy LM configuration."""
    dspy.settings.configure(lm=None)


__all__ = ["configure_lm_from_env", "reset_lm"]
