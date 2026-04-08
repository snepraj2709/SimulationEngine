import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreateRequest
from app.schemas.product import ProductUnderstandingSchema


def test_user_create_schema_validates_email() -> None:
    with pytest.raises(ValidationError):
        UserCreateRequest(email="invalid", password="StrongPass123!", full_name="Bad Email")


def test_product_understanding_schema_accepts_expected_payload() -> None:
    payload = ProductUnderstandingSchema(
        company_name="Netflix",
        product_name="Netflix Streaming Subscription",
        category="Consumer Subscription Software",
        subcategory="Video Streaming",
        positioning_summary="Subscription-based entertainment streaming platform",
        pricing_model="tiered_subscription",
        feature_clusters=["content library access"],
        monetization_hypothesis="Recurring monthly subscription revenue",
        target_customer_signals=["mobile-first viewers"],
        confidence_score=0.88,
        confidence_scores={"category": 0.9},
        warnings=[],
        summary_line="Streaming entertainment subscription for households and individual viewers.",
        buyer_type="Household and individual viewers",
        sales_motion="Self-serve plans",
        review_status="ready",
        business_model_signals=[
            {
                "key": "pricing_visibility",
                "label": "Pricing Visibility",
                "value": "High",
                "score_1_to_5": 5,
                "confidence": 0.9,
                "editable": True,
            }
        ],
        customer_logic={
            "core_job_to_be_done": "Watch a broad entertainment catalog without managing cable bundles.",
            "why_they_buy": ["Affordable entertainment", "Wide content access"],
            "why_they_hesitate": ["Subscription overlap"],
            "what_it_replaces": ["cable bundles"],
        },
        monetization_model={
            "pricing_visibility": "high",
            "pricing_model": "tiered_subscription",
            "monetization_hypothesis": "Recurring monthly subscription revenue",
            "sales_motion": "Self-serve plans",
        },
        feature_cluster_details=[
            {"key": "content-library", "label": "content library access", "importance": "high", "description": "Streaming content breadth."}
        ],
        simulation_levers=[
            {
                "key": "pricing",
                "label": "Pricing",
                "why_it_matters": "Price changes affect conversion and churn.",
                "confidence": 0.88,
                "editable": True,
            }
        ],
        uncertainties=[],
        source_coverage={
            "fields_observed_explicitly": ["Pricing visibility"],
            "fields_inferred": [],
            "fields_missing": [],
        },
    )
    assert payload.confidence_score == 0.88
