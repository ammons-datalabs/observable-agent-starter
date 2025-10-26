"""Configuration helpers for the Influencer Assistant example."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Sequence

import dspy

from observable_agent_starter.agents.routing import config

configure_lm_from_env_base = config.configure_lm_from_env
log_langfuse_generation = config.log_langfuse_generation

from influencer_assistant.profile import InfluencerProfile


def configure_lm_from_env() -> bool:
    """Delegate to the shared triage LM configurator."""

    return configure_lm_from_env_base()


def reset_lm() -> None:
    """Reset DSPy LM configuration."""

    dspy.settings.configure(lm=None)


def log_video_ideas(
    *,
    profile: InfluencerProfile,
    request: str,
    ideas: Sequence[object],
    variation_token: str | None,
    fallback_reason: str | None = None,
) -> None:
    """Send an observation describing the generated video ideas to Langfuse."""

    payload = {
        "creator_id": profile.creator_id,
        "handle": profile.handle,
        "ideas": [asdict(idea) if is_dataclass(idea) else idea for idea in ideas],
    }

    metadata = {
        key: value
        for key, value in {
            "variation_token": variation_token,
            "fallback_reason": fallback_reason,
        }.items()
        if value
    }

    log_langfuse_generation(
        name="influencer-video-ideas",
        input_text=request,
        output_payload=payload,
        metadata=metadata or None,
    )
