from __future__ import annotations

import json
from pathlib import Path

import dspy
import pytest

from influencer_assistant.dspy import VideoIdeaGenerator, render_profile_context
from influencer_assistant.profile import InfluencerProfile, InfluencerProfileBuilder
import influencer_assistant.dspy.video_ideas as video_ideas_module

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "creator_snapshot.json"


@pytest.fixture(scope="module")
def profile() -> InfluencerProfile:
    payload = json.loads(FIXTURE_PATH.read_text())
    builder = InfluencerProfileBuilder()
    profile = builder.build(payload)
    return profile


@pytest.fixture(autouse=True)
def disable_langfuse_logging(monkeypatch):
    monkeypatch.setattr(video_ideas_module, "log_video_ideas", lambda **_: None)


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
    dspy.settings.configure(lm=None)

    captured: dict[str, list[dict]] = {"calls": []}

    def _capture(**kwargs):
        captured["calls"].append(kwargs)

    monkeypatch.setattr(video_ideas_module, "log_video_ideas", _capture)

    generator = VideoIdeaGenerator(target_count=2)
    ideas = list(generator(profile, request="Fallback please"))

    assert len(ideas) == 2
    assert all(idea.pillar for idea in ideas)
    assert captured["calls"]
    assert captured["calls"][0]["fallback_reason"] == "no_lm"
