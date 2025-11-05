"""Core data structures and builders for the influencer portfolio."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field


class InfluencerProfile(BaseModel):
    """Normalized view of a managed creator business."""

    creator_id: str
    handle: str
    name: str
    description: str
    niche: str
    monetization: Optional[str] = None
    goals: Dict[str, Any]
    audience: Dict[str, Any]
    content_pillars: List[str]
    publishing_cadence: Dict[str, Any]
    backlog: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    operations: Dict[str, Any] = Field(default_factory=dict)
    community: Dict[str, Any] = Field(default_factory=dict)
    experiments: List[Dict[str, Any]] = Field(default_factory=list)
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class InfluencerProfileBuilder:
    """Aggregates multiple inputs into an `InfluencerProfile`."""

    def __init__(self, llm_runner: Any | None = None) -> None:
        self._llm_runner = llm_runner

    def build(self, inputs: Dict[str, Any]) -> InfluencerProfile:
        identity = inputs.get("creator_identity", {}) or {}
        analytics = inputs.get("analytics", {}) or {}
        content = inputs.get("content_library", {}) or {}
        call_notes = inputs.get("call_notes", []) or []
        research = inputs.get("market_research", {}) or {}
        operations = inputs.get("operations", {}) or {}
        community = inputs.get("community", {}) or {}
        experiments = list(inputs.get("experiments", []) or [])
        asset_library = list(inputs.get("asset_library", []) or [])
        workflows = list(inputs.get("workflows", []) or [])

        profile = InfluencerProfile(
            creator_id=identity.get("creator_id", ""),
            handle=identity.get("handle", ""),
            name=identity.get("name", ""),
            description=identity.get("description", ""),
            niche=identity.get("niche", ""),
            monetization=identity.get("monetization"),
            goals=self._build_goals(identity=identity, analytics=analytics),
            audience=self._build_audience(research.get("audience")),
            content_pillars=list(content.get("pillars", []) or []),
            publishing_cadence=self._build_publishing_cadence(analytics.get("upload_frequency")),
            backlog=self._build_backlog(
                call_notes=call_notes,
                upcoming_ideas=content.get("upcoming_ideas"),
                workflow_tasks=workflows,
            ),
            risks=self._detect_risks(analytics=analytics),
            operations=self._build_operations(operations),
            community=self._build_community(community),
            experiments=self._build_experiments(experiments),
            assets=self._build_assets(asset_library),
            raw=inputs,
        )

        return profile

    @staticmethod
    def _build_goals(identity: Dict[str, Any], analytics: Dict[str, Any]) -> Dict[str, Any]:
        goals: Dict[str, Any] = {
            "primary": identity.get("primary_goal", ""),
            "secondary": identity.get("secondary_goals", []),
        }

        metrics = {
            key: analytics.get(key)
            for key in (
                "subscribers",
                "views_last_28_days",
                "avg_view_duration_seconds",
            )
            if analytics.get(key) is not None
        }
        if metrics:
            goals["metrics"] = metrics

        return goals

    @staticmethod
    def _build_audience(raw_audience: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not raw_audience:
            return {}

        audience = {
            "persona": raw_audience.get("persona", ""),
            "pain_points": list(raw_audience.get("pain_points", []) or []),
            "desired_outcomes": list(raw_audience.get("desired_outcomes", []) or []),
        }
        return audience

    @classmethod
    def _build_backlog(
        cls,
        *,
        call_notes: Iterable[Dict[str, Any]],
        upcoming_ideas: Optional[Iterable[Dict[str, Any]]],
        workflow_tasks: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        backlog: List[Dict[str, Any]] = []

        for note in call_notes:
            actions = note.get("action_items") or []
            if not actions:
                continue
            backlog.append(
                {
                    "type": "call_followup",
                    "source_date": note.get("date"),
                    "summary": note.get("summary"),
                    "actions": list(actions),
                }
            )

        for idea in upcoming_ideas or []:
            backlog.append(
                {
                    "type": "content_idea",
                    "title": idea.get("title", ""),
                    "status": idea.get("status", ""),
                    "notes": idea.get("notes", ""),
                }
            )

        for task in workflow_tasks or []:
            backlog.append(
                {
                    "type": "workflow_task",
                    "title": task.get("title", ""),
                    "status": task.get("status", ""),
                    "due_date": task.get("due_date"),
                    "owner": task.get("owner"),
                    "notes": task.get("notes", ""),
                }
            )

        return backlog

    @staticmethod
    def _build_publishing_cadence(frequency: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not frequency:
            return {}
        return {
            "planned_per_week": frequency.get("planned_per_week"),
            "actual_last_28_days": frequency.get("actual_last_28_days"),
        }

    @staticmethod
    def _detect_risks(analytics: Dict[str, Any]) -> List[str]:
        risks: List[str] = []
        frequency = analytics.get("upload_frequency") or {}
        planned = frequency.get("planned_per_week")
        actual = frequency.get("actual_last_28_days")
        if isinstance(planned, (int, float)) and isinstance(actual, (int, float)):
            # Normalize actual uploads in the last 28 days to a weekly rate for comparison.
            actual_per_week = actual / 4 if actual else 0
            if actual_per_week < planned:
                risks.append("Publishing cadence is below plan")

        return risks

    @staticmethod
    def _build_operations(operations: Dict[str, Any]) -> Dict[str, Any]:
        if not operations:
            return {}

        return {
            "owner": operations.get("owner"),
            "talent_manager": operations.get("talent_manager"),
            "strategist": operations.get("strategist"),
            "editor_pod": list(operations.get("editor_pod", []) or []),
            "additional_team": list(operations.get("additional_team", []) or []),
            "timezone": operations.get("timezone"),
            "automation_notes": operations.get("automation_notes"),
            "integrations": list(operations.get("integrations", []) or []),
        }

    @staticmethod
    def _build_community(community: Dict[str, Any]) -> Dict[str, Any]:
        if not community:
            return {}

        return {
            "sentiment": community.get("sentiment"),
            "response_sla_hours": community.get("response_sla_hours"),
            "pending_replies": community.get("pending_replies", 0),
            "highlighted_threads": list(community.get("highlighted_threads", []) or []),
            "macros": list(community.get("macros", []) or []),
            "notes": community.get("notes"),
        }

    @staticmethod
    def _build_experiments(experiments: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        built: List[Dict[str, Any]] = []
        for experiment in experiments or []:
            built.append(
                {
                    "name": experiment.get("name", ""),
                    "hypothesis": experiment.get("hypothesis"),
                    "metric": experiment.get("metric"),
                    "status": experiment.get("status", ""),
                    "latest_result": experiment.get("latest_result"),
                    "next_check_in": experiment.get("next_check_in"),
                }
            )
        return built

    @staticmethod
    def _build_assets(assets: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        built: List[Dict[str, Any]] = []
        for asset in assets or []:
            built.append(
                {
                    "asset_type": asset.get("asset_type", ""),
                    "title": asset.get("title", ""),
                    "url": asset.get("url", ""),
                    "notes": asset.get("notes"),
                }
            )
        return built
