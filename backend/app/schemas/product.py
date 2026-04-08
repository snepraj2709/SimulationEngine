from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

ReviewStatus = Literal["ready", "needs_review"]
FeatureImportance = Literal["high", "medium", "low"]
UncertaintySeverity = Literal["high", "medium", "low"]


class ProductBusinessSignalResponse(BaseModel):
    key: str
    label: str
    value: str
    score_1_to_5: int | None = Field(default=None, ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    editable: bool = True


class ProductCustomerLogicResponse(BaseModel):
    core_job_to_be_done: str
    why_they_buy: list[str] = Field(default_factory=list)
    why_they_hesitate: list[str] = Field(default_factory=list)
    what_it_replaces: list[str] = Field(default_factory=list)


class ProductMonetizationModelResponse(BaseModel):
    pricing_visibility: str
    pricing_model: str
    monetization_hypothesis: str
    sales_motion: str


class ProductFeatureClusterResponse(BaseModel):
    key: str
    label: str
    importance: FeatureImportance
    description: str | None = None


class ProductSimulationLeverResponse(BaseModel):
    key: str
    label: str
    why_it_matters: str
    confidence: float = Field(ge=0, le=1)
    editable: bool = True


class ProductUncertaintyResponse(BaseModel):
    key: str
    label: str
    reason: str
    severity: UncertaintySeverity
    needs_user_review: bool = True


class ProductSourceCoverageResponse(BaseModel):
    fields_observed_explicitly: list[str] = Field(default_factory=list)
    fields_inferred: list[str] = Field(default_factory=list)
    fields_missing: list[str] = Field(default_factory=list)


class ProductUnderstandingViewModelResponse(BaseModel):
    id: str
    company_name: str
    product_name: str
    summary_line: str
    category: str
    subcategory: str
    confidence: float = Field(ge=0, le=1)
    review_status: ReviewStatus
    business_model_signals: list[ProductBusinessSignalResponse] = Field(default_factory=list)
    customer_logic: ProductCustomerLogicResponse
    monetization_model: ProductMonetizationModelResponse
    feature_clusters: list[ProductFeatureClusterResponse] = Field(default_factory=list)
    simulation_levers: list[ProductSimulationLeverResponse] = Field(default_factory=list)
    uncertainties: list[ProductUncertaintyResponse] = Field(default_factory=list)
    source_coverage: ProductSourceCoverageResponse


class ProductUnderstandingSchema(BaseModel):
    company_name: str
    product_name: str
    category: str
    subcategory: str
    positioning_summary: str
    pricing_model: str
    feature_clusters: list[str]
    monetization_hypothesis: str
    target_customer_signals: list[str]
    confidence_score: float = Field(ge=0, le=1)
    confidence_scores: dict[str, float]
    warnings: list[str] = Field(default_factory=list)
    summary_line: str
    buyer_type: str
    sales_motion: str
    review_status: ReviewStatus
    business_model_signals: list[ProductBusinessSignalResponse] = Field(default_factory=list)
    customer_logic: ProductCustomerLogicResponse
    monetization_model: ProductMonetizationModelResponse
    feature_cluster_details: list[ProductFeatureClusterResponse] = Field(default_factory=list)
    simulation_levers: list[ProductSimulationLeverResponse] = Field(default_factory=list)
    uncertainties: list[ProductUncertaintyResponse] = Field(default_factory=list)
    source_coverage: ProductSourceCoverageResponse


class ExtractedProductDataResponse(ORMModel):
    id: str
    analysis_id: str
    company_name: str
    product_name: str
    category: str
    subcategory: str
    positioning_summary: str
    pricing_model: str
    monetization_hypothesis: str
    raw_extracted_json: dict
    normalized_json: dict
    view_model: ProductUnderstandingViewModelResponse
    confidence_score: float
    is_user_edited: bool = False
    edited_at: datetime | None = None


class ProductUnderstandingUpdateRequest(BaseModel):
    company_name: str
    product_name: str
    summary_line: str
    category: str
    subcategory: str
    buyer_type: str
    business_model_signals: list[ProductBusinessSignalResponse] = Field(default_factory=list, max_length=10)
    customer_logic: ProductCustomerLogicResponse
    monetization_model: ProductMonetizationModelResponse
    feature_clusters: list[ProductFeatureClusterResponse] = Field(min_length=1, max_length=6)
    simulation_levers: list[ProductSimulationLeverResponse] = Field(default_factory=list, max_length=6)
    uncertainties: list[ProductUncertaintyResponse] = Field(default_factory=list, max_length=6)
