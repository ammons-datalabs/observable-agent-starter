from __future__ import annotations

import logging
from typing import Any, Dict

import dspy

from .config import configure_lm_from_env, log_langfuse_generation
from .policy import neutral_policy

LOGGER = logging.getLogger(__name__)
ALLOWED_ROUTES = {"billing", "tech", "sales"}

class RouteRequestSignature(dspy.Signature):
    """Route an incoming request to one of: {billing, tech, sales}."""

    request = dspy.InputField(desc="User-submitted request text")
    route = dspy.OutputField(desc="One of {billing, tech, sales}")
    rationale = dspy.OutputField(desc="Very short reasoning for the decision")

class StarterAgent(dspy.Module):
    """Starter agent for request routing with observability.

    This is the template agent you'll customize for your use case.
    Routes requests to billing, tech, or sales departments.
    """
    def __init__(self):
        super().__init__()
        # Ensure LM is configured before constructing DSPy modules that may inspect settings
        configure_lm_from_env()
        self.route = dspy.ChainOfThought(RouteRequestSignature)

    def forward(self, request: str) -> Dict[str, Any]:
        configure_lm_from_env()

        # Be tolerant of different dspy versions: check both getter and attribute
        lm_obj = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
        if lm_obj is None:
            lm_obj = getattr(dspy.settings, "lm", None)

        if lm_obj is None:
            route = neutral_policy(request)
            return {
                "route": route,
                "explanation": "Policy fallback used because no LM is configured.",
            }

        pred = self.route(request=request)

        raw_route = getattr(pred, "route", "")
        if isinstance(raw_route, str):
            raw_route = raw_route.strip().lower()
        explanation = getattr(pred, "rationale", "") or getattr(pred, "explanation", "")

        fallback_reason: str | None = None
        if raw_route not in ALLOWED_ROUTES:
            LOGGER.warning("Invalid route '%s' returned by LM; applying neutral policy", raw_route)
            raw_route = neutral_policy(request)
            fallback_reason = "invalid_route"
            explanation = "Policy fallback applied because LM returned an unsupported route."

        result = {"route": raw_route, "explanation": explanation}

        log_langfuse_generation(
            name="routing-agent",
            input_text=request,
            output_payload=result,
            metadata={"fallback_reason": fallback_reason} if fallback_reason else None,
        )

        return result

# Backward compatibility alias
ExampleAgent = StarterAgent

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = StarterAgent()
    example = "The invoice shows an extra fee on my account."
    # Prefer calling the module directly to avoid DSPy warnings about .forward
    print(agent(request=example))
