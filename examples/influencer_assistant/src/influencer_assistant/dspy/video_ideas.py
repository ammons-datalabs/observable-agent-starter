"""DSPy module for generating video ideas from a creator portfolio.

Demonstrates composition pattern with ObservabilityProvider from observable_agent_starter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Sequence

import dspy

from observable_agent_starter import ObservabilityProvider
from influencer_assistant.profile import InfluencerProfile

from .context import render_profile_context
from .config import configure_lm_from_env


@dataclass
class VideoIdea:
    """Structured representation of a suggested video idea."""

    title: str
    summary: str
    pillar: str | None = None


class VideoIdeaSignature(dspy.Signature):
    """Formulate new video ideas for a creator-led brand."""

    profile_context = dspy.InputField(desc="Key details about the creator business")
    request = dspy.InputField(desc="Manager request or constraints")
    response = dspy.OutputField(
        desc=("Return exactly 3 numbered lines, each formatted as: " "'Title - Summary | Pillar'.")
    )


class VideoIdeaGenerator(dspy.Module):
    """Generate video ideas grounded in a `InfluencerProfile`.

    Uses composition pattern with ObservabilityProvider for tracing.
    """

    def __init__(self, observability: ObservabilityProvider, *, target_count: int = 4) -> None:
        super().__init__()
        self.observability = observability
        self.predict = dspy.Predict(VideoIdeaSignature)
        self._target_count = target_count

    def forward(
        self,
        profile: InfluencerProfile,
        *,
        request: str = "Generate topical video ideas",
        variation_token: str | None = None,
    ) -> Sequence[VideoIdea]:
        configure_lm_from_env()

        profile_context = render_profile_context(profile)
        variation_hint = (
            f" Variation token: {variation_token}. Use it to provide fresh, non-repeated ideas and do not mention the token in the response."
            if variation_token
            else ""
        )
        fallback_reason = None

        if dspy.settings.lm is None:
            ideas = _fallback_ideas(
                profile=profile,
                request=request,
                max_ideas=self._target_count,
            )
            fallback_reason = "no_lm"
        else:
            prediction = self.predict(
                profile_context=profile_context,
                request=(
                    f"Provide {self._target_count} concise video ideas that align with the request: {request}. "
                    "Return them as a numbered list where each item includes a title, target pillar, and a short summary separated by ' - '."
                    + variation_hint
                ),
            )
            ideas = _parse_ideas(
                prediction.response,
                default_pillars=profile.content_pillars,
                max_ideas=self._target_count,
            )

            if not ideas:
                ideas = _fallback_ideas(
                    profile=profile,
                    request=request,
                    max_ideas=self._target_count,
                )
                fallback_reason = "empty_response"

        # Log via ObservabilityProvider
        self.observability.log_generation(
            input_data={"profile": profile.handle, "request": request},
            output_data={
                "creator_id": profile.creator_id,
                "handle": profile.handle,
                "ideas": [asdict(idea) for idea in ideas],
            },
            variation_token=variation_token,
            fallback_reason=fallback_reason,
        )

        return ideas


def _parse_ideas(
    text: str,
    *,
    default_pillars: Sequence[str],
    max_ideas: int,
) -> List[VideoIdea]:
    ideas: List[VideoIdea] = []
    current_pillar_index = 0

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Remove numbering like "1." or "1)"
        if line and line[0].isdigit():
            line = line.lstrip("0123456789). ")

        pillar = None
        summary = ""
        title = line

        # Preferred format: Title - Summary | Pillar
        if "|" in line:
            left, pillar = [part.strip() for part in line.rsplit("|", maxsplit=1)]
        else:
            left = line

        if " - " in left:
            title, summary = [part.strip() for part in left.split(" - ", maxsplit=1)]
        else:
            title = left.strip()

        if not pillar and default_pillars:
            pillar = default_pillars[current_pillar_index % len(default_pillars)]
            current_pillar_index += 1

        ideas.append(
            VideoIdea(
                title=title or "Idea",
                summary=summary or "Fill in details",
                pillar=pillar,
            )
        )

    return ideas[: max(1, max_ideas)]


def _fallback_ideas(
    *,
    profile: InfluencerProfile,
    request: str,
    max_ideas: int,
) -> List[VideoIdea]:
    """Generate deterministic fallback ideas when no LM output is available."""

    ideas: List[VideoIdea] = []
    pillars = profile.content_pillars or ["Strategy"]
    base_titles = [
        "Playbook Spotlight",
        "Behind-the-Scenes Ops",
        "Automation Boost",
        "Community Wins",
    ]

    for idx in range(max_ideas):
        pillar = pillars[idx % len(pillars)]
        title = f"{pillar} {base_titles[idx % len(base_titles)]}"
        summary = f"Actionable idea inspired by the '{pillar}' pillar to address: {request}."
        ideas.append(
            VideoIdea(
                title=title,
                summary=summary,
                pillar=pillar,
            )
        )

    return ideas


class VideoIdeasStructuredSignature(dspy.Signature):
    """Structured output: exactly 3 ideas (title, summary, pillar)."""

    profile_context = dspy.InputField(desc="Key details about the creator business")
    request = dspy.InputField(desc="Manager request or constraints")

    idea1_title = dspy.OutputField(desc="Idea 1 title")
    idea1_summary = dspy.OutputField(desc="Idea 1 short summary (one clause)")
    idea1_pillar = dspy.OutputField(desc="Idea 1 content pillar label")

    idea2_title = dspy.OutputField(desc="Idea 2 title")
    idea2_summary = dspy.OutputField(desc="Idea 2 short summary (one clause)")
    idea2_pillar = dspy.OutputField(desc="Idea 2 content pillar label")

    idea3_title = dspy.OutputField(desc="Idea 3 title")
    idea3_summary = dspy.OutputField(desc="Idea 3 short summary (one clause)")
    idea3_pillar = dspy.OutputField(desc="Idea 3 content pillar label")
