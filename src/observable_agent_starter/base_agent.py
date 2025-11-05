"""Observability provider for agents using composition pattern."""

import logging
from typing import Any, Dict, Optional
from .config import configure_lm_from_env, log_langfuse_generation

LOGGER = logging.getLogger(__name__)


class ObservabilityProvider:
    """Provides observability and tracing capabilities via composition.

    Designed to be injected into agents as a dependency rather than
    inherited via multiple inheritance.

    Example usage:
        from observable_agent_starter import ObservabilityProvider, create_observability
        import dspy

        class MyAgent(dspy.Module):
            def __init__(self, observability: ObservabilityProvider):
                super().__init__()
                self.observability = observability
                self.predict = dspy.ChainOfThought(MySignature)

            def forward(self, **kwargs):
                result = self.predict(**kwargs)
                self.observability.log_generation(
                    input_data=kwargs,
                    output_data={"result": result.output}
                )
                return result

        # Create and use agent
        observability = create_observability("my-agent")
        agent = MyAgent(observability=observability)
    """

    def __init__(self, observation_name: str):
        """Initialize with Langfuse observation name.

        Args:
            observation_name: Name for Langfuse traces (e.g. "my-agent")
        """
        self.observation_name = observation_name
        self.logger = LOGGER.getChild(observation_name)

    def log_generation(
        self,
        input_data: Any,
        output_data: Dict[str, Any],
        **metadata
    ) -> None:
        """Helper to log generation to Langfuse.

        Args:
            input_data: Input to the agent (will be converted to string)
            output_data: Output from the agent (dict)
            **metadata: Additional metadata to include in trace
        """
        log_langfuse_generation(
            name=self.observation_name,
            input_text=str(input_data),
            output_payload=output_data,
            metadata=metadata or None
        )


def create_observability(observation_name: str, *, configure_lm: bool = True) -> ObservabilityProvider:
    """Factory function to create an ObservabilityProvider with optional LM configuration.

    Args:
        observation_name: Name for Langfuse traces (e.g. "my-agent")
        configure_lm: Whether to auto-configure LM from environment (default: True)

    Returns:
        Configured ObservabilityProvider instance

    Example:
        observability = create_observability("my-agent")
        agent = MyAgent(observability=observability)
    """
    observability = ObservabilityProvider(observation_name)

    if configure_lm:
        configured = configure_lm_from_env()
        if configured:
            observability.logger.info("LM configured")
        else:
            observability.logger.warning("No LM configured; agent may need fallback")

    return observability
