"""Streamlit dashboard for the Influencer Assistant example."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

import dspy
import streamlit as st

EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = EXAMPLE_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from observable_agent_starter import create_observability  # noqa: E402
from influencer_assistant.dspy import (  # noqa: E402
    VideoIdeaGenerator,
    configure_lm_from_env,
    render_profile_context,
)
from influencer_assistant.profile import InfluencerProfile, InfluencerProfileBuilder  # noqa: E402

FIXTURES_DIR = EXAMPLE_ROOT / "tests" / "fixtures"
DEFAULT_REQUEST = "Ideas that grow high-quality inbound leads"
FALLBACK_IDEAS = (
    "1. Systems Sprint Recap - Share wins from recent workflow experiments | Behind-the-scenes ops\n"
    "2. Creator Ops Playbook - Highlight packaged services and outcomes | Agency growth playbooks\n"
    "3. Automation Toolkit Tour - Walk through the current AI stack | AI tooling deep dives"
)


@st.cache_data
def list_fixture_paths() -> List[Path]:
    return sorted(FIXTURES_DIR.glob("creator_snapshot*.json"))


@st.cache_data
def load_snapshot(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text())


def format_option_label(path: Path, payload: Dict[str, object]) -> str:
    name = payload.get("creator_identity", {}).get("name")
    if not name:
        name = path.stem.replace("creator_snapshot", "").replace("_", " ").strip() or path.stem
    return f"{name} ({payload.get('creator_identity', {}).get('handle', 'unknown')})"


def ensure_language_model() -> str:
    if configure_lm_from_env():
        return "Using configured language model"

    if dspy.settings.lm is None:
        dspy.settings.configure(lm=dspy.utils.DummyLM([{ "response": FALLBACK_IDEAS }]))
        return "Using fallback dummy responses"

    return "Using existing language model"


def render_highlights(payload: Dict[str, object]) -> None:
    analytics = payload.get("analytics", {}) or {}
    cadence = (analytics.get("upload_frequency") or {})
    cols = st.columns(3)
    cols[0].metric("Subscribers", f"{analytics.get('subscribers', 0):,}")
    cols[1].metric("Views (28d)", f"{analytics.get('views_last_28_days', 0):,}")
    planned = cadence.get("planned_per_week")
    actual = cadence.get("actual_last_28_days")
    cols[2].metric("Cadence", f"{actual or 0} vs plan {planned or '—'}")


def render_profile_sections(profile: InfluencerProfile) -> None:
    st.subheader("Creator Operations Snapshot")
    col_a, col_b = st.columns(2)
    col_a.markdown("**Content Pillars**")
    for pillar in profile.content_pillars:
        col_a.write(f"• {pillar}")

    col_b.markdown("**Risks & Experiments**")
    if profile.risks:
        for risk in profile.risks:
            col_b.warning(risk)
    else:
        col_b.info("No risks detected")

    if profile.experiments:
        with st.expander("Active Experiments", expanded=False):
            for experiment in profile.experiments:
                name = experiment.get("name", "Experiment")
                summary = experiment.get("latest_result", experiment.get("status", ""))
                st.write(f"**{name}** — {summary}")

    with st.expander("Team & Operations"):
        ops = profile.operations
        st.write(f"Owner: {ops.get('owner', '—')}")
        st.write(f"Talent manager: {ops.get('talent_manager', '—')}")
        st.write(f"Strategist: {ops.get('strategist', '—')}")
        if ops.get("editor_pod"):
            st.write("Editor pod: " + ", ".join(ops["editor_pod"]))
        if ops.get("integrations"):
            st.write("Integrations: " + ", ".join(ops["integrations"]))


def render_idea_generation(profile: InfluencerProfile) -> None:
    st.subheader("Assistant: Video Idea Generator")
    ensure_status = ensure_language_model()
    st.caption(ensure_status)

    with st.form("idea-generator"):
        request = st.text_input("What should the assistant focus on?", value=DEFAULT_REQUEST)
        target_count = st.slider("How many ideas?", min_value=2, max_value=5, value=3)
        variation_token = st.text_input("Variation token (optional)")
        submitted = st.form_submit_button("Generate ideas")

    if submitted:
        observability = create_observability("influencer-video-ideas", configure_lm=False)
        generator = VideoIdeaGenerator(observability=observability, target_count=target_count)
        ideas = list(
            generator(
                profile,
                request=request,
                variation_token=variation_token or None,
            )
        )
        if not ideas:
            st.info("No ideas returned. Try adjusting the request.")
            return

        for idx, idea in enumerate(ideas, start=1):
            pillar = f" ({idea.pillar})" if idea.pillar else ""
            st.markdown(f"**{idx}. {idea.title}{pillar}**")
            st.write(idea.summary)

        with st.expander("Prompt context" , expanded=False):
            st.code(render_profile_context(profile), language="markdown")


def render_raw_profile(profile: InfluencerProfile) -> None:
    with st.expander("Raw profile JSON", expanded=False):
        st.json(profile.model_dump())


def main() -> None:
    st.set_page_config(page_title="Influencer Assistant", layout="wide")
    st.title("Influencer Assistant Dashboard")

    fixture_paths = list_fixture_paths()
    if not fixture_paths:
        st.error("No creator snapshot fixtures found.")
        return

    builder = InfluencerProfileBuilder()

    options = []
    for path in fixture_paths:
        payload = load_snapshot(path)
        options.append((format_option_label(path, payload), path, payload))

    selected_label = st.sidebar.selectbox(
        "Select a creator snapshot", [label for label, _, _ in options]
    )
    selected_path, payload = next((p, data) for label, p, data in options if label == selected_label)

    profile = builder.build(payload)

    st.sidebar.markdown("### Snapshot metadata")
    st.sidebar.write(f"Creator ID: {profile.creator_id}")
    st.sidebar.write(f"Handle: {profile.handle}")
    st.sidebar.write(f"Primary goal: {profile.goals.get('primary', '—')}")

    render_highlights(payload)
    render_profile_sections(profile)
    render_idea_generation(profile)
    render_raw_profile(profile)


if __name__ == "__main__":
    main()
