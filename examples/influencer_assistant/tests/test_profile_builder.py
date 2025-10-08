"""Unit tests for the influencer portfolio builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pytest

from influencer_assistant.profile import InfluencerProfile, InfluencerProfileBuilder

FIXTURES = [
    Path(__file__).resolve().parent / "fixtures" / name
    for name in (
        "creator_snapshot.json",
        "creator_snapshot_growth_guild.json",
        "creator_snapshot_creator_lab.json",
    )
]


@pytest.fixture(params=FIXTURES)
def portfolio_inputs(request) -> Dict:
    fixture_path: Path = request.param
    return json.loads(fixture_path.read_text())


def test_builds_normalized_profile(portfolio_inputs: Dict[str, object]) -> None:
    builder = InfluencerProfileBuilder(llm_runner=None)

    profile = builder.build(portfolio_inputs)

    assert isinstance(profile, InfluencerProfile)
    assert profile.creator_id
    assert profile.handle.startswith("@")
    assert profile.content_pillars
    assert profile.publishing_cadence is not None
    assert profile.backlog  # backlog should exist with followups/tasks/ideas
    assert profile.operations is not None
    assert profile.community is not None
    assert profile.raw["creator_identity"]["creator_id"] == profile.creator_id


def test_operations_and_community_sections_populate(portfolio_inputs: Dict[str, object]) -> None:
    builder = InfluencerProfileBuilder()
    profile = builder.build(portfolio_inputs)

    operations = profile.operations
    community = profile.community

    # Operations should include either team composition or integrations
    assert set(operations.keys()) >= {"editor_pod", "integrations"}
    assert isinstance(operations.get("editor_pod"), list)

    # Community data should expose engagement KPIs
    assert "pending_replies" in community
    assert community.get("pending_replies") >= 0


def test_experiments_and_assets_roundtrip(portfolio_inputs: Dict[str, object]) -> None:
    builder = InfluencerProfileBuilder()
    profile = builder.build(portfolio_inputs)

    # Experiments list should match raw payload counts
    raw_experiments = portfolio_inputs.get("experiments", [])
    assert len(profile.experiments) == len(raw_experiments)

    for experiment in profile.experiments:
        assert experiment["name"]
        assert experiment["status"]

    # Asset pointers carry type/title/url for downstream tools
    for asset in profile.assets:
        assert {"asset_type", "title", "url"}.issubset(asset)
        assert asset["url"].startswith("http")


def test_risk_detection_flags_cadence_issue() -> None:
    inputs = json.loads((FIXTURES[0]).read_text())
    builder = InfluencerProfileBuilder()

    profile = builder.build(inputs)

    assert any("cadence" in risk.lower() for risk in profile.risks)
