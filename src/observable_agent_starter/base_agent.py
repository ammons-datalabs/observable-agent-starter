"""Minimal base agent providing config and tracing hooks."""

import logging
from typing import Any, Dict
from .config import configure_lm_from_env, log_langfuse_generation

LOGGER = logging.getLogger(__name__)


class BaseAgent:
    """Thin base providing config + observability hooks.

    Does NOT impose DSPy patterns or business logic.
    Examples own their own DSPy signatures, fallback policies, etc.

    Example usage:
        from observable_agent_starter import BaseAgent
        import dspy

        class MyAgent(dspy.Module, BaseAgent):
            def __init__(self):
                dspy.Module.__init__(self)
                BaseAgent.__init__(self, observation_name="my-agent")
                self.predict = dspy.ChainOfThought(MySignature)

            def forward(self, **kwargs):
                result = self.predict(**kwargs)
                self.log_generation(
                    input_data=kwargs,
                    output_data={"result": result.output}
                )
                return result
    """

    def __init__(self, observation_name: str):
        """Initialize with Langfuse observation name.

        Args:
            observation_name: Name for Langfuse traces (e.g. "my-agent")
        """
        self.observation_name = observation_name
        self.logger = LOGGER.getChild(observation_name)

        # Auto-configure LM from environment
        configured = configure_lm_from_env()
        if configured:
            self.logger.info("LM configured")
        else:
            self.logger.warning("No LM configured; agent may need fallback")

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
