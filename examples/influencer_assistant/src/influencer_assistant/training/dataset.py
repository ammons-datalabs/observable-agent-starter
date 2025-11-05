"""Training data for tuning the Influencer Assistant DSPy modules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

import dspy

from influencer_assistant.dspy.context import render_profile_context
from influencer_assistant.profile import InfluencerProfile, InfluencerProfileBuilder

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"


PILLARS = {
    "AI tooling deep dives",
    "Agency growth playbooks",
    "Behind-the-scenes ops",
    "Enterprise growth playbooks",
    "Live show replays",
    "Tooling breakdowns",
    "Automation walk-throughs",
    "Template showcases",
    "Creator case studies",
}


def _std_title(s: str) -> str:
    s = s.strip()
    # Title case light touch
    return s[:1].upper() + s[1:]


def _std_summary(s: str) -> str:
    s = s.strip()
    # One clause, remove trailing periods
    if s.endswith("."):
        s = s[:-1]
    return s


def _std_pillar(p: str) -> str:
    p = p.strip()
    # Normalize known variants
    variants = {
        "Automation walkthroughs": "Automation walk-throughs",
        "Automation walk throughs": "Automation walk-throughs",
        "Behind the scenes ops": "Behind-the-scenes ops",
    }
    p = variants.get(p, p)
    return p


def _validate_and_standardize(ideas: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if len(ideas) != 3:
        raise ValueError("Each label must include exactly 3 ideas.")
    out: List[Dict[str, str]] = []
    for i, obj in enumerate(ideas, start=1):
        title = _std_title(obj.get("title", "").strip())
        summary = _std_summary(obj.get("summary", "").strip())
        pillar = _std_pillar(obj.get("pillar", "").strip())
        if not title or not summary or not pillar:
            raise ValueError(f"Idea {i} missing title/summary/pillar")
        if pillar not in PILLARS:
            raise ValueError(f"Idea {i} uses unknown pillar: {pillar}")
        out.append({"title": title, "summary": summary, "pillar": pillar})
    return out


@dataclass
class IdeaTrainingExample:
    """Container for a single idea-generation training record."""

    fixture: str
    request: str
    expected_ideas: List[Dict[str, str]]


# Curated expectations derived from the synthetic fixtures. The responses are written in
# the same numbered-list style we ask the LM to produce.
_RAW_EXAMPLES: List[IdeaTrainingExample] = [
    IdeaTrainingExample(
        fixture="creator_snapshot.json",
        request="Develop videos that fuel service-qualified leads",
        expected_ideas=_validate_and_standardize(
            [
                {
                    "title": "Automating Onboarding Wins",
                    "summary": "Showcase the AI SOP playbook with proof points",
                    "pillar": "AI tooling deep dives",
                },
                {
                    "title": "Case Study Sprint",
                    "summary": "Highlight recent client outcomes and ROI",
                    "pillar": "Agency growth playbooks",
                },
                {
                    "title": "Pipeline Q&A",
                    "summary": "Answer common lead objections with actionable advice",
                    "pillar": "Behind-the-scenes ops",
                },
            ]
        ),
    ),
    IdeaTrainingExample(
        fixture="creator_snapshot.json",
        request="Behind-the-scenes ops that build trust",
        expected_ideas=_validate_and_standardize(
            [
                {
                    "title": "SOP Breakdown Live",
                    "summary": "Walk through a real client SOP handoff with commentary",
                    "pillar": "Behind-the-scenes ops",
                },
                {
                    "title": "Weekly Ops Standup",
                    "summary": "Share the team's async sprint board and priorities",
                    "pillar": "Behind-the-scenes ops",
                },
                {
                    "title": "From Inquiry to Intake",
                    "summary": "Demo the lead-to-onboarding workflow with key touchpoints",
                    "pillar": "Behind-the-scenes ops",
                },
            ]
        ),
    ),
    IdeaTrainingExample(
        fixture="creator_snapshot_growth_guild.json",
        request="Ideas that reinforce enterprise credibility",
        expected_ideas=_validate_and_standardize(
            [
                {
                    "title": "Enterprise Funnel Teardown",
                    "summary": "Walk through a successful client campaign",
                    "pillar": "Enterprise growth playbooks",
                },
                {
                    "title": "Live ABM Lab",
                    "summary": "Preview the upcoming teardown show with concrete KPIs",
                    "pillar": "Live show replays",
                },
                {
                    "title": "Operations Dashboard Tour",
                    "summary": "Demo the RevOps dashboards used with clients",
                    "pillar": "Tooling breakdowns",
                },
            ]
        ),
    ),
    IdeaTrainingExample(
        fixture="creator_snapshot_growth_guild.json",
        request="Prove pipeline impact to skeptical VPs",
        expected_ideas=_validate_and_standardize(
            [
                {
                    "title": "SQL Uplift Postmortem",
                    "summary": "Decompose an experiment that moved qualified pipeline",
                    "pillar": "Enterprise growth playbooks",
                },
                {
                    "title": "Attribution Deep Dive",
                    "summary": "Show how we stitched multi-touch to defend budget",
                    "pillar": "Tooling breakdowns",
                },
                {
                    "title": "C-Suite Metrics Pack",
                    "summary": "Share the exact exec dashboard used in reviews",
                    "pillar": "Live show replays",
                },
            ]
        ),
    ),
    IdeaTrainingExample(
        fixture="creator_snapshot_creator_lab.json",
        request="Focus on automation hacks for shorts teams",
        expected_ideas=_validate_and_standardize(
            [
                {
                    "title": "Caption Automation Shootout",
                    "summary": "Compare AI caption tools with results",
                    "pillar": "Automation walk-throughs",
                },
                {
                    "title": "Batch Script Workflow",
                    "summary": "Reveal the team's template system for scripts",
                    "pillar": "Template showcases",
                },
                {
                    "title": "Community Challenge Recap",
                    "summary": "Share standout creations from the Discord",
                    "pillar": "Creator case studies",
                },
            ]
        ),
    ),
    IdeaTrainingExample(
        fixture="creator_snapshot_creator_lab.json",
        request="Drive more template pack conversions",
        expected_ideas=_validate_and_standardize(
            [
                {
                    "title": "3 Templates, 3 Outcomes",
                    "summary": "Showcase before/after clips using best-sellers",
                    "pillar": "Template showcases",
                },
                {
                    "title": "10-Minute Remix Flow",
                    "summary": "Automate cuts, captions, and exports end-to-end",
                    "pillar": "Automation walk-throughs",
                },
                {
                    "title": "Customer Wall of Wins",
                    "summary": "Compile short testimonials with overlays",
                    "pillar": "Creator case studies",
                },
            ]
        ),
    ),
]


def _load_profile(fixture_name: str) -> InfluencerProfile:
    builder = InfluencerProfileBuilder()
    payload = json.loads((FIXTURES_DIR / fixture_name).read_text())
    return builder.build(payload)


def build_training_dataset() -> List[dspy.Example]:
    """Return DSPy examples ready for teleprompting."""

    examples: List[dspy.Example] = []

    for record in _RAW_EXAMPLES:
        profile = _load_profile(record.fixture)
        context = render_profile_context(profile)
        ideas = _validate_and_standardize(record.expected_ideas)
        # Map to structured output fields expected by the structured signature
        fields = {
            "profile_context": context,
            "request": record.request,
            "idea1_title": ideas[0]["title"],
            "idea1_summary": ideas[0]["summary"],
            "idea1_pillar": ideas[0]["pillar"],
            "idea2_title": ideas[1]["title"],
            "idea2_summary": ideas[1]["summary"],
            "idea2_pillar": ideas[1]["pillar"],
            "idea3_title": ideas[2]["title"],
            "idea3_summary": ideas[2]["summary"],
            "idea3_pillar": ideas[2]["pillar"],
        }
        examples.append(dspy.Example(**fields).with_inputs("profile_context", "request"))

    return examples


__all__ = ["build_training_dataset", "IdeaTrainingExample"]
