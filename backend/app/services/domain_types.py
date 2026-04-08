from typing import Literal

from pydantic import BaseModel, Field


class ScrapeResult(BaseModel):
    source_url: str
    final_url: str
    title: str
    meta_description: str
    headings: list[str] = Field(default_factory=list)
    paragraphs: list[str] = Field(default_factory=list)
    feature_clues: list[str] = Field(default_factory=list)
    pricing_clues: list[str] = Field(default_factory=list)
    audience_clues: list[str] = Field(default_factory=list)
    category_clues: list[str] = Field(default_factory=list)
    raw_text: str
    raw_extracted_json: dict = Field(default_factory=dict)
    fetch_source: str = "network"


ReviewStatus = Literal["ready", "needs_review"]
FeatureImportance = Literal["high", "medium", "low"]
UncertaintySeverity = Literal["high", "medium", "low"]


class BusinessModelSignal(BaseModel):
    key: str
    label: str
    value: str
    score_1_to_5: int | None = Field(default=None, ge=1, le=5)
    confidence: float = Field(default=0.5, ge=0, le=1)
    editable: bool = True


class CustomerLogic(BaseModel):
    core_job_to_be_done: str = ""
    why_they_buy: list[str] = Field(default_factory=list)
    why_they_hesitate: list[str] = Field(default_factory=list)
    what_it_replaces: list[str] = Field(default_factory=list)


class MonetizationModel(BaseModel):
    pricing_visibility: str = "low"
    pricing_model: str = "usage_or_custom"
    monetization_hypothesis: str = ""
    sales_motion: str = ""


class FeatureCluster(BaseModel):
    key: str
    label: str
    importance: FeatureImportance = "medium"
    description: str | None = None


class SimulationLever(BaseModel):
    key: str
    label: str
    why_it_matters: str
    confidence: float = Field(default=0.5, ge=0, le=1)
    editable: bool = True


class UncertaintyItem(BaseModel):
    key: str
    label: str
    reason: str
    severity: UncertaintySeverity = "medium"
    needs_user_review: bool = True


class SourceCoverage(BaseModel):
    fields_observed_explicitly: list[str] = Field(default_factory=list)
    fields_inferred: list[str] = Field(default_factory=list)
    fields_missing: list[str] = Field(default_factory=list)


class ProductUnderstanding(BaseModel):
    company_name: str
    product_name: str
    category: str
    subcategory: str
    positioning_summary: str
    pricing_model: str
    feature_clusters: list[str]
    monetization_hypothesis: str
    target_customer_signals: list[str]
    confidence_score: float
    confidence_scores: dict[str, float]
    warnings: list[str] = Field(default_factory=list)
    raw_extracted_json: dict = Field(default_factory=dict)
    normalized_json: dict = Field(default_factory=dict)
    summary_line: str = ""
    buyer_type: str = ""
    sales_motion: str = ""
    review_status: ReviewStatus = "ready"
    business_model_signals: list[BusinessModelSignal] = Field(default_factory=list)
    customer_logic: CustomerLogic = Field(default_factory=CustomerLogic)
    monetization_model: MonetizationModel = Field(default_factory=MonetizationModel)
    feature_cluster_details: list[FeatureCluster] = Field(default_factory=list)
    simulation_levers: list[SimulationLever] = Field(default_factory=list)
    uncertainties: list[UncertaintyItem] = Field(default_factory=list)
    source_coverage: SourceCoverage = Field(default_factory=SourceCoverage)


class GeneratedICP(BaseModel):
    name: str
    description: str
    use_case: str
    goals: list[str]
    pain_points: list[str]
    decision_drivers: list[str]
    driver_weights: dict[str, float]
    price_sensitivity: float
    switching_cost: float
    alternatives: list[str]
    churn_threshold: float
    retention_threshold: float
    adoption_friction: float
    value_perception_explanation: str
    segment_weight: float


class GeneratedScenario(BaseModel):
    title: str
    scenario_type: str
    description: str
    input_parameters: dict


class SimulationComputationResult(BaseModel):
    reaction: str
    utility_score_before: float
    utility_score_after: float
    delta_score: float
    revenue_delta: float
    perception_shift: float
    second_order_effects: list[str]
    driver_impacts: dict[str, float]
    explanation: str
    assumptions: dict


class AggregatedScenarioOutcome(BaseModel):
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
