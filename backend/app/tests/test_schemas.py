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
    )
    assert payload.confidence_score == 0.88
