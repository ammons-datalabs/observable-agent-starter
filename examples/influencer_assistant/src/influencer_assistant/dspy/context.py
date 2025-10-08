"""Utilities for rendering influencer profiles into prompt context."""

from __future__ import annotations

from typing import List

from influencer_assistant.profile import InfluencerProfile


def _format_section(title: str, lines: List[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines if line)
    return f"{title}:\n{body}\n" if body else ""


def render_profile_context(profile: InfluencerProfile) -> str:
    """Summarize an `InfluencerProfile` for use in DSPy prompts."""

    parts: List[str] = []

    parts.append(
        _format_section(
            "Creator Identity",
            [
                f"Name: {profile.name}",
                f"Handle: {profile.handle}",
                f"Niche: {profile.niche}",
                f"Primary goal: {profile.goals.get('primary')}",
                f"Secondary goals: {', '.join(profile.goals.get('secondary', []))}",
                f"Monetization: {profile.monetization or 'N/A'}",
            ],
        )
    )

    audience = profile.audience or {}
    parts.append(
        _format_section(
            "Audience",
            [
                f"Persona: {audience.get('persona', 'N/A')}",
                f"Pain points: {', '.join(audience.get('pain_points', []))}",
                f"Desired outcomes: {', '.join(audience.get('desired_outcomes', []))}",
            ],
        )
    )

    parts.append(
        _format_section(
            "Content Pillars",
            profile.content_pillars,
        )
    )

    if profile.operations:
        parts.append(
            _format_section(
                "Team",
                [
                    f"Owner: {profile.operations.get('owner', 'N/A')}",
                    f"Talent manager: {profile.operations.get('talent_manager', 'N/A')}",
                    f"Strategist: {profile.operations.get('strategist', 'N/A')}",
                    f"Editor pod: {', '.join(profile.operations.get('editor_pod', [])) or 'N/A'}",
                    f"Key integrations: {', '.join(profile.operations.get('integrations', [])) or 'None'}",
                ],
            )
        )

    if profile.community:
        parts.append(
            _format_section(
                "Community",
                [
                    f"Sentiment: {profile.community.get('sentiment', 'N/A')}",
                    f"Pending replies: {profile.community.get('pending_replies', 0)}",
                    f"Macros: {', '.join(profile.community.get('macros', [])) or 'None'}",
                ],
            )
        )

    if profile.experiments:
        experiment_lines = [
            f"{exp['name']} ({exp['status']}): metric={exp.get('metric') or 'N/A'}"
            for exp in profile.experiments
        ]
        parts.append(_format_section("Experiments", experiment_lines))

    if profile.risks:
        parts.append(_format_section("Risks", profile.risks))

    return "\n".join(part for part in parts if part).strip()
