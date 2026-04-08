from app.services.product_understanding_service import ProductUnderstandingService
from app.tests.factories import sample_product_understanding, sample_scrape_result


def test_build_from_normalized_backfills_new_business_view_from_legacy_payload() -> None:
    service = ProductUnderstandingService()
    legacy_payload = {
        "company_name": "Acme",
        "product_name": "Acme Growth Platform",
        "category": "B2B Software",
        "subcategory": "Revenue Operations",
        "positioning_summary": "Acme helps revenue teams automate onboarding and renewals.",
        "pricing_model": "sales_led_custom_pricing",
        "feature_clusters": ["workflow automation", "renewal analytics"],
        "monetization_hypothesis": "Annual contracts from revenue teams.",
        "target_customer_signals": ["revenue teams"],
        "confidence_score": 0.78,
        "confidence_scores": {
            "company_name": 0.9,
            "summary_line": 0.82,
            "category": 0.8,
            "buyer_type": 0.74,
            "customer_logic": 0.72,
            "pricing_model": 0.7,
            "monetization_model": 0.7,
            "feature_clusters": 0.84,
            "business_model_signals": 0.74,
            "simulation_levers": 0.68,
        },
        "warnings": [],
        "raw_extracted_json": sample_scrape_result().raw_extracted_json,
    }

    understanding = service.build_from_normalized(legacy_payload)

    assert understanding.summary_line == "Acme helps revenue teams automate onboarding and renewals."
    assert understanding.business_model_signals[0].key == "buyer_type"
    assert understanding.monetization_model.sales_motion == "Demo-led / enterprise sales"
    assert understanding.feature_cluster_details[0].label == "workflow automation"
    assert understanding.simulation_levers


def test_finalize_derives_uncertainties_when_pricing_is_not_public() -> None:
    service = ProductUnderstandingService()
    scrape = sample_scrape_result().model_copy(
        update={
            "pricing_clues": [],
            "raw_extracted_json": {
                **sample_scrape_result().raw_extracted_json,
                "pricing_clues": [],
                "buttons": ["Book a demo"],
            },
        }
    )

    understanding = service.build(scrape)

    assert any(item.key == "pricing_visibility" for item in understanding.uncertainties)
    assert understanding.review_status == "needs_review"
    assert any(lever.key == "proof_case_studies" for lever in understanding.simulation_levers)


def test_finalize_preserves_field_confidence_scores() -> None:
    understanding = sample_product_understanding()
    rebuilt = ProductUnderstandingService().build_from_normalized(understanding.normalized_json)

    assert rebuilt.confidence_scores["summary_line"] == understanding.confidence_scores["summary_line"]
    assert rebuilt.confidence_scores["buyer_type"] == understanding.confidence_scores["buyer_type"]
    assert rebuilt.business_model_signals[0].confidence == understanding.business_model_signals[0].confidence
