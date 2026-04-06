from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


ReactionLiteral = Literal["retain", "upgrade", "downgrade", "churn"]


class ICPProfileResponse(ORMModel):
    id: str
    analysis_id: str
    name: str
    description: str
    use_case: str
    goals_json: list[str]
    pain_points_json: list[str]
    decision_drivers_json: list[str]
    driver_weights_json: dict[str, float]
    price_sensitivity: float
    switching_cost: float
    alternatives_json: list[str]
    churn_threshold: float
    retention_threshold: float
    adoption_friction: float
    value_perception_explanation: str
    segment_weight: float


class ScenarioResponse(ORMModel):
    id: str
    analysis_id: str
    title: str
    scenario_type: str
    description: str
    input_parameters_json: dict
    created_at: datetime
    updated_at: datetime


class SimulationResultResponse(ORMModel):
    id: str
    simulation_run_id: str
    icp_profile_id: str
    reaction: ReactionLiteral
    utility_score_before: float
    utility_score_after: float
    delta_score: float
    revenue_delta: float
    perception_shift: float
    second_order_effects_json: list[str]
    driver_impacts_json: dict[str, float]
    explanation: str
    created_at: datetime


class ScenarioSimulationSummary(BaseModel):
    scenario_id: str
    scenario_title: str
    projected_retention_pct: float
    projected_downgrade_pct: float
    projected_upgrade_pct: float
    projected_churn_pct: float
    estimated_revenue_delta_pct: float
    weighted_revenue_delta: float
    perception_shift_score: float
    perception_shift_label: str
    highest_risk_icps: list[str]
    top_negative_drivers: list[str]
    top_positive_drivers: list[str]
    second_order_effects: list[str]


class SimulationRunResponse(ORMModel):
    id: str
    analysis_id: str
    scenario_id: str
    run_version: str
    engine_version: str
    assumptions_json: dict
    created_at: datetime
    results: list[SimulationResultResponse] = Field(default_factory=list)
    summary: ScenarioSimulationSummary


class SimulateScenarioRequest(BaseModel):
    input_overrides: dict = Field(default_factory=dict)
    run_version: str = "1"


class DriverImpactBreakdown(BaseModel):
    driver: str
    impact: float

