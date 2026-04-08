from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


ReactionLiteral = Literal["retain", "upgrade", "downgrade", "churn"]
SignalLevelLiteral = Literal[1, 2, 3, 4, 5]
ConfidenceLabelLiteral = Literal["low", "medium", "high"]
ConfidenceSourceLiteral = Literal["llm", "derived"]
EditableControlLiteral = Literal["text", "textarea", "percentage", "dot_scale", "ranked_driver_editor"]
ImpactSeverityLiteral = Literal["high", "medium", "low"]
ImpactDirectionLiteral = Literal["positive", "negative", "mixed", "neutral"]
EffortLevelLiteral = Literal["low", "medium", "high"]


class ConfidenceIndicatorResponse(BaseModel):
    score: float = Field(ge=0, le=1)
    label: ConfidenceLabelLiteral
    source: ConfidenceSourceLiteral


class EditableFieldConfigResponse(BaseModel):
    field: str
    label: str
    control: EditableControlLiteral
    editable: bool = True
    visible_by_default: bool = True
    min: float | None = None
    max: float | None = None


class ICPBuyingLogicResponse(BaseModel):
    buys_for: list[str] = Field(default_factory=list)
    avoids_because: list[str] = Field(default_factory=list)
    wins_with: list[str] = Field(default_factory=list)


class BehavioralSignalResponse(BaseModel):
    signal_key: str
    label: str
    value_1_to_5: SignalLevelLiteral
    editable: bool
    derived: bool = False
    source_field: str | None = None


class DecisionDriverViewResponse(BaseModel):
    key: str
    label: str
    weight_percent: int = Field(ge=0, le=100)
    rank: int = Field(ge=1)


class SimulationImpactItemResponse(BaseModel):
    title: str
    explanation: str
    severity: ImpactSeverityLiteral = "medium"


class ICPViewModelResponse(BaseModel):
    id: str
    segment_name: str
    segment_summary: str
    estimated_segment_share: float = Field(ge=0, le=100)
    confidence: ConfidenceIndicatorResponse | None = None
    best_fit_use_case: str
    buying_logic: ICPBuyingLogicResponse
    behavioral_signals: list[BehavioralSignalResponse] = Field(default_factory=list)
    decision_drivers: list[DecisionDriverViewResponse] = Field(default_factory=list)
    simulation_impact: list[SimulationImpactItemResponse] = Field(default_factory=list)
    editable_fields: list[EditableFieldConfigResponse] = Field(default_factory=list)


class ICPProfileResponse(ORMModel):
    id: str
    analysis_id: str
    display_order: int
    is_user_edited: bool
    edited_at: datetime | None
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
    view_model: ICPViewModelResponse | None = None


class ScenarioInputFieldResponse(BaseModel):
    key: str
    label: str
    input_type: Literal["text", "number"]
    required: bool
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    placeholder: str | None = None
    helper_text: str | None = None


class ScenarioInputSchemaResponse(BaseModel):
    fields: list[ScenarioInputFieldResponse] = Field(default_factory=list)


class ScenarioRecommendationResponse(BaseModel):
    priority_rank: int = Field(ge=1)
    recommendation_label: str
    recommendation_reason: str


class ScenarioExpectedImpactResponse(BaseModel):
    metric_key: str
    label: str
    direction: ImpactDirectionLiteral
    min_change_percent: float
    max_change_percent: float
    confidence: ConfidenceLabelLiteral | None = None


class ScenarioExecutionEffortResponse(BaseModel):
    level: EffortLevelLiteral
    explanation: str


class ScenarioLinkedICPSummaryResponse(BaseModel):
    segment_name: str
    relevant_signals: list[BehavioralSignalResponse] = Field(default_factory=list)


class ScenarioMetadataResponse(BaseModel):
    market: str | None = None
    service_name: str | None = None
    plan_tier: str | None = None
    billing_period: str | None = None
    scenario_tags: list[str] = Field(default_factory=list)


class ScenarioReviewViewResponse(BaseModel):
    id: str
    scenario_type: str
    scenario_title: str
    scenario_summary: str
    short_decision_statement: str
    recommendation: ScenarioRecommendationResponse
    expected_impact: list[ScenarioExpectedImpactResponse] = Field(default_factory=list)
    why_this_might_work: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    execution_effort: ScenarioExecutionEffortResponse
    linked_icp_summary: ScenarioLinkedICPSummaryResponse | None = None
    raw_parameters: dict = Field(default_factory=dict)
    metadata: ScenarioMetadataResponse


class ScenarioResponse(ORMModel):
    id: str
    analysis_id: str
    display_order: int
    is_user_edited: bool
    edited_at: datetime | None
    title: str
    scenario_type: str
    description: str
    input_parameters_json: dict
    input_parameters_schema: ScenarioInputSchemaResponse
    created_at: datetime
    updated_at: datetime
    review_view: ScenarioReviewViewResponse | None = None


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


class DriverWeightUpdateRequest(BaseModel):
    driver: str
    weight: float = Field(ge=0)


class ICPProfileUpdateRequest(BaseModel):
    name: str
    description: str
    use_case: str
    goals: list[str] = Field(min_length=1, max_length=6)
    pain_points: list[str] = Field(min_length=1, max_length=6)
    decision_drivers: list[str] = Field(min_length=3, max_length=6)
    driver_weights: list[DriverWeightUpdateRequest] = Field(min_length=3, max_length=6)
    price_sensitivity: float
    switching_cost: float
    alternatives: list[str] = Field(min_length=1, max_length=6)
    churn_threshold: float
    retention_threshold: float
    adoption_friction: float
    value_perception_explanation: str
    segment_weight: float


class ScenarioUpdateRequest(BaseModel):
    title: str
    scenario_type: str
    description: str
    input_parameters: dict = Field(default_factory=dict)
