from __future__ import annotations

import json
from pathlib import Path

import dspy
import pytest

from influencer_assistant.dspy import VideoIdeaGenerator, render_profile_context
from influencer_assistant.profile import InfluencerProfile, InfluencerProfileBuilder
from observable_agent_starter import BaseAgent

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "creator_snapshot.json"


@pytest.fixture(scope="module")
def profile() -> InfluencerProfile:
    payload = json.loads(FIXTURE_PATH.read_text())
    builder = InfluencerProfileBuilder()
    profile = builder.build(payload)
    return profile


@pytest.fixture(autouse=True)
def disable_langfuse_logging(monkeypatch):
    monkeypatch.setattr(BaseAgent, "log_generation", lambda self, **_: None)


@pytest.fixture(autouse=True)
def configure_dummy_lm():
    dspy.settings.configure(lm=dspy.utils.DummyLM([
        {
            "response": (
                "1. Automating Onboarding Results - Highlight our AI SOPs | AI tooling deep dives\n"
                "2. Turning Views Into Leads - Showcase success stories | Agency growth playbooks"
            )
        }
    ]))
    yield
    dspy.settings.configure(lm=None)


def test_render_profile_context_contains_core_sections(profile: InfluencerProfile) -> None:
    context = render_profile_context(profile)
    assert "Creator Identity" in context
    assert "Content Pillars" in context
    assert "Risks" in context


def test_video_idea_generator_parses_dummy_response(profile: InfluencerProfile) -> None:
    generator = VideoIdeaGenerator(target_count=2)
    ideas = list(generator(profile, request="Focus on lead gen"))

    assert len(ideas) == 2
    assert ideas[0].title.startswith("Automating Onboarding")
    assert ideas[0].summary  # should not be empty
    assert ideas[0].pillar == "AI tooling deep dives"
    assert "success stories" in ideas[1].summary


def test_video_idea_generator_fallback_without_lm(monkeypatch, profile: InfluencerProfile) -> None:
    # Prevent configure_lm_from_env from loading LM - patch at base_agent module level
    import observable_agent_starter.base_agent as base_agent_module
    monkeypatch.setattr(base_agent_module, "configure_lm_from_env", lambda: False)

    # Also patch it in video_ideas module
    import influencer_assistant.dspy.video_ideas as video_ideas_module
    monkeypatch.setattr(video_ideas_module, "configure_lm_from_env", lambda: False)

    dspy.settings.configure(lm=None)

    captured: dict[str, list[dict]] = {"calls": []}

    def _capture(self, **kwargs):
        captured["calls"].append(kwargs)

    monkeypatch.setattr(BaseAgent, "log_generation", _capture)

    generator = VideoIdeaGenerator(target_count=2)
    ideas = list(generator(profile, request="Fallback please"))

    assert len(ideas) == 2
    assert all(idea.pillar for idea in ideas)
    assert captured["calls"]
    # metadata items are passed as **kwargs to log_generation
    assert captured["calls"][0]["fallback_reason"] == "no_lm"
