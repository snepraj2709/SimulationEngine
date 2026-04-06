from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


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
    confidence_score: float
