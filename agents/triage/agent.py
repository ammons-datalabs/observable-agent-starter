from __future__ import annotations

import logging
from typing import Any, Dict

import dspy

from .config import configure_lm_from_env, log_langfuse_generation
from .policy import neutral_policy

LOGGER = logging.getLogger(__name__)
ALLOWED_ROUTES = {"billing", "tech", "sales"}

class TriageSignature(dspy.Signature):
    """Route an incoming ticket neutrally to one of: {billing, tech, sales}."""

    ticket = dspy.InputField(desc="User-submitted support ticket text")
    route = dspy.OutputField(desc="One of {billing, tech, sales}")
    rationale = dspy.OutputField(desc="Very short reasoning for the decision")

class TriageAgent(dspy.Module):
    def __init__(self):
        super().__init__()
        # Ensure LM is configured before constructing DSPy modules that may inspect settings
        configure_lm_from_env()
        self.route = dspy.ChainOfThought(TriageSignature)

    def forward(self, ticket: str) -> Dict[str, Any]:
        configure_lm_from_env()

        # Be tolerant of different dspy versions: check both getter and attribute
        lm_obj = dspy.settings.get("lm") if hasattr(dspy.settings, "get") else None
        if lm_obj is None:
            lm_obj = getattr(dspy.settings, "lm", None)

        if lm_obj is None:
            route = neutral_policy(ticket)
            return {
                "route": route,
                "explanation": "Policy fallback used because no LM is configured.",
            }

        pred = self.route(ticket=ticket)

        raw_route = getattr(pred, "route", "")
        if isinstance(raw_route, str):
            raw_route = raw_route.strip().lower()
        explanation = getattr(pred, "rationale", "") or getattr(pred, "explanation", "")

        fallback_reason: str | None = None
        if raw_route not in ALLOWED_ROUTES:
            LOGGER.warning("Invalid route '%s' returned by LM; applying neutral policy", raw_route)
            raw_route = neutral_policy(ticket)
            fallback_reason = "invalid_route"
            explanation = "Policy fallback applied because LM returned an unsupported route."

        result = {"route": raw_route, "explanation": explanation}

        log_langfuse_generation(
            name="triage-agent",
            input_text=ticket,
            output_payload=result,
            metadata={"fallback_reason": fallback_reason} if fallback_reason else None,
        )

        return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    triager = TriageAgent()
    example = "The invoice shows an extra fee on my account."
    # Prefer calling the module directly to avoid DSPy warnings about .forward
    print(triager(ticket=example))
