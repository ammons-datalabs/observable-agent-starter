"""DeepEval quality metrics for video idea generation."""

import os
from pathlib import Path
import pytest
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval import assert_test
from dotenv import load_dotenv

from influencer_assistant.dspy.video_ideas import VideoIdeaGenerator
from influencer_assistant.profile import InfluencerProfile
from observable_agent_starter import create_observability

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="DeepEval requires OPENAI_API_KEY"
)


@pytest.fixture
def generator():
    observability = create_observability("eval-video-ideas", configure_lm=False)
    return VideoIdeaGenerator(observability=observability)


@pytest.fixture
def test_profile():
    return InfluencerProfile(
        creator_id="test-001",
        handle="@testcreator",
        name="Test Creator",
        description="A tech creator focused on productivity and AI tools",
        niche="Tech & Productivity",
        content_pillars=["AI Tools", "Productivity", "Creator Economy"],
        goals={
            "primary": "Reach 100k subscribers",
            "secondary": ["Build a course", "Launch a community"]
        },
        audience={
            "persona": "Tech-savvy professionals and creators",
            "pain_points": ["Time management", "Tool overwhelm"],
            "desired_outcomes": ["Work smarter", "Build audience"]
        },
        publishing_cadence={
            "planned_per_week": 3,
            "actual_last_28_days": 10
        }
    )


def test_relevancy_to_request(generator, test_profile):
    """Video ideas should be relevant to the request."""
    ideas = generator(
        profile=test_profile,
        request="Generate ideas about AI productivity tools for creators"
    )

    actual_output = "\n".join([
        f"{i.title}: {i.summary}"
        for i in ideas
    ])

    test_case = LLMTestCase(
        input="Generate ideas about AI productivity tools for creators",
        actual_output=actual_output,
        expected_output="AI productivity tools for creators"
    )

    metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [metric])


def test_faithfulness_to_profile(generator, test_profile):
    """Ideas should be grounded in creator's content pillars."""
    ideas = generator(
        profile=test_profile,
        request="Generate video ideas"
    )

    actual_output = "\n".join([
        f"{i.title}: {i.summary}"
        for i in ideas
    ])

    retrieval_context = [
        f"Content pillars: {', '.join(test_profile.content_pillars)}",
        f"Niche: {test_profile.niche}",
        f"Creator: {test_profile.handle}"
    ]

    test_case = LLMTestCase(
        input="Generate video ideas",
        actual_output=actual_output,
        retrieval_context=retrieval_context
    )

    metric = FaithfulnessMetric(threshold=0.7)
    assert_test(test_case, [metric])


def test_pillar_adherence(generator, test_profile):
    """Generated ideas should map to content pillars."""
    ideas = generator(profile=test_profile, request="Generate video ideas")

    # Check that each idea has a valid pillar
    for idea in ideas:
        assert idea.pillar in test_profile.content_pillars, \
            f"Idea pillar '{idea.pillar}' not in profile pillars {test_profile.content_pillars}"
