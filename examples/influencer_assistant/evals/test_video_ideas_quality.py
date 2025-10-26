"""DeepEval quality metrics for video idea generation."""

import os
import pytest
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval import assert_test

from influencer_assistant.dspy.video_ideas import VideoIdeaGenerator
from influencer_assistant.profile import InfluencerProfile

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="DeepEval requires OPENAI_API_KEY"
)


@pytest.fixture
def generator():
    return VideoIdeaGenerator()


@pytest.fixture
def test_profile():
    return InfluencerProfile(
        creator_id="test-001",
        handle="@testcreator",
        niche="Tech & Productivity",
        content_pillars=["AI Tools", "Productivity", "Creator Economy"]
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
