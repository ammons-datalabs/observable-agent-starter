import os

import pytest
from deepeval.metrics import AnswerRelevancyMetric
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from agents.example.agent import ExampleAgent


def test_policy_fallback_handles_billing_request():
    agent = ExampleAgent()
    out = agent.forward("The invoice shows an extra fee")
    assert out["route"] == "billing"


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="AnswerRelevancyMetric requires an OpenAI API key",
)
def test_basic_relevance_with_deepeval():
    agent = ExampleAgent()
    out = agent.forward("The invoice shows an extra fee")
    metric = AnswerRelevancyMetric()
    test_case = LLMTestCase(
        input="The invoice shows an extra fee",
        actual_output=out["route"],
        expected_output="billing",
    )
    assert_test(test_case=test_case, metrics=[metric])
