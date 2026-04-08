from types import SimpleNamespace

import pytest

from app.core.exceptions import AppException
from app.schemas.product import ProductUnderstandingUpdateRequest
from app.services.llm.openai_analysis_service import (
    AnalysisArtifactsResponse,
    ConfidenceScoresResponse,
    DriverWeightResponse,
    GeneratedICPResponse,
    GeneratedScenarioResponse,
    OpenAIAnalysisService,
    ProductCustomerLogicResponse,
    ProductFeatureClusterResponse,
    ProductUnderstandingResponse,
    ScenarioInputParametersResponse,
)
from app.tests.factories import sample_scrape_result


def sample_product_payload(**overrides) -> ProductUnderstandingResponse:
    payload = ProductUnderstandingResponse(
        company_name="Acme",
        product_name="Acme Growth Platform",
        summary_line="Acme helps revenue teams automate onboarding and renewal workflows.",
        category="B2B Software",
        subcategory="Revenue Operations",
        buyer_type="Revenue and customer success teams",
        sales_motion="Demo-led / enterprise sales",
        pricing_model="sales_led_custom_pricing",
        monetization_hypothesis="Annual contracts from revenue teams.",
        customer_logic=ProductCustomerLogicResponse(
            core_job_to_be_done="Automate onboarding and renewal workflows.",
            why_they_buy=["Reduce manual work", "Improve renewal visibility"],
            why_they_hesitate=["Implementation complexity", "Pricing is not fully visible"],
            what_it_replaces=["spreadsheets", "point tools"],
        ),
        feature_clusters=[
            ProductFeatureClusterResponse(label="workflow automation", importance="high", description="Automates lifecycle work."),
            ProductFeatureClusterResponse(label="renewal analytics", importance="high", description="Tracks renewal health."),
            ProductFeatureClusterResponse(label="workflow automation", importance="medium", description="Duplicate for dedupe checks."),
        ],
        confidence_score=0.88,
        confidence_scores=ConfidenceScoresResponse(
            company_name=0.9,
            summary_line=0.88,
            category=0.84,
            buyer_type=0.87,
            customer_logic=0.83,
            pricing_model=0.88,
            monetization_model=0.86,
            feature_clusters=0.88,
            business_model_signals=0.8,
            simulation_levers=0.78,
        ),
    )
    return payload.model_copy(update=overrides)


def test_normalize_product_understanding_builds_normalized_payload() -> None:
    service = OpenAIAnalysisService()
    payload = sample_product_payload()

    understanding = service._normalize_product_understanding(payload, sample_scrape_result())

    assert understanding.company_name == "Acme"
    assert understanding.normalized_json["company_name"] == "Acme"
    assert understanding.feature_clusters == ["workflow automation", "renewal analytics"]
    assert understanding.confidence_scores["pricing_model"] == pytest.approx(0.88)
    assert understanding.business_model_signals[0].key == "buyer_type"
    assert understanding.simulation_levers
    assert understanding.review_status == "needs_review"


def test_normalize_product_understanding_preserves_full_editable_text_fields() -> None:
    service = OpenAIAnalysisService()
    long_summary_line = (
        "Acme helps revenue teams automate onboarding, expansion, and lifecycle orchestration across product, sales, "
        "and customer success with a unified workspace that connects health signals, playbooks, approvals, "
        "stakeholder collaboration, and revenue-risk insights without forcing teams into separate point solutions."
    )
    long_pricing_model = (
        "Likely SaaS subscription with a free entry option, annual volume discounts, optional premium support, "
        "and custom enterprise pricing for larger rollouts."
    )
    payload = sample_product_payload(summary_line=long_summary_line, pricing_model=long_pricing_model)

    understanding = service._normalize_product_understanding(payload, sample_scrape_result())

    assert understanding.positioning_summary == long_summary_line
    assert understanding.pricing_model == long_pricing_model
    assert not understanding.positioning_summary.endswith("...")
    assert not understanding.pricing_model.endswith("...")


def test_normalize_product_understanding_update_preserves_full_editable_text_fields() -> None:
    service = OpenAIAnalysisService()
    existing = service._normalize_product_understanding(
        sample_product_payload(summary_line="Short summary"),
        sample_scrape_result(),
    )
    updated_summary_line = (
        "Acme now positions itself as an end-to-end operating system for revenue execution, giving customer success, "
        "sales, and finance a shared workflow for lifecycle planning, renewal forecasting, account interventions, "
        "and expansion playbooks from one coordinated system."
    )
    updated_pricing_model = (
        "Usage-aware subscription with a self-serve starting tier, team-based packaging, and custom enterprise pricing "
        "for procurement-heavy accounts."
    )

    understanding = service.normalize_product_understanding_update(
        ProductUnderstandingUpdateRequest(
            company_name="Acme",
            product_name="Acme Growth Platform",
            summary_line=updated_summary_line,
            category="B2B Software",
            subcategory="Revenue Operations",
            buyer_type="Revenue and customer success teams",
            business_model_signals=[item.model_dump() for item in existing.business_model_signals],
            customer_logic=existing.customer_logic.model_dump(),
            monetization_model={
                "pricing_visibility": "medium",
                "pricing_model": updated_pricing_model,
                "monetization_hypothesis": "Annual contracts from revenue teams.",
                "sales_motion": "Demo-led / enterprise sales",
            },
            feature_clusters=[item.model_dump() for item in existing.feature_cluster_details],
            simulation_levers=[item.model_dump() for item in existing.simulation_levers],
            uncertainties=[item.model_dump() for item in existing.uncertainties],
        ),
        existing=existing,
    )

    assert understanding.positioning_summary == updated_summary_line
    assert understanding.pricing_model == updated_pricing_model
    assert not understanding.positioning_summary.endswith("...")
    assert not understanding.pricing_model.endswith("...")


def test_normalize_analysis_artifacts_renormalizes_weights() -> None:
    service = OpenAIAnalysisService()
    payload = AnalysisArtifactsResponse(
        icps=[
            GeneratedICPResponse(
                name="ICP 1",
                description="desc",
                use_case="use case",
                goals=["goal 1", "goal 2"],
                pain_points=["pain 1", "pain 2"],
                decision_drivers=["price_affordability", "automation_coverage", "analytics_depth"],
                driver_weights=[
                    DriverWeightResponse(driver="price_affordability", weight=2),
                    DriverWeightResponse(driver="automation_coverage", weight=1),
                    DriverWeightResponse(driver="analytics_depth", weight=1),
                ],
                price_sensitivity=1.4,
                switching_cost=-0.2,
                alternatives=["manual"],
                churn_threshold=-0.5,
                retention_threshold=0.4,
                adoption_friction=1.4,
                value_perception_explanation="explanation",
                segment_weight=5,
            ),
            GeneratedICPResponse(
                name="ICP 2",
                description="desc",
                use_case="use case",
                goals=["goal 1", "goal 2"],
                pain_points=["pain 1", "pain 2"],
                decision_drivers=["team_enablement", "support_reliability", "feature_completeness"],
                driver_weights=[
                    DriverWeightResponse(driver="team_enablement", weight=0),
                    DriverWeightResponse(driver="support_reliability", weight=0),
                    DriverWeightResponse(driver="feature_completeness", weight=0),
                ],
                price_sensitivity=0.4,
                switching_cost=0.3,
                alternatives=["competitor"],
                churn_threshold=-0.2,
                retention_threshold=0.05,
                adoption_friction=0.2,
                value_perception_explanation="explanation",
                segment_weight=3,
            ),
            GeneratedICPResponse(
                name="ICP 3",
                description="desc",
                use_case="use case",
                goals=["goal 1", "goal 2"],
                pain_points=["pain 1", "pain 2"],
                decision_drivers=["budget_predictability", "implementation_complexity", "price_affordability"],
                driver_weights=[
                    DriverWeightResponse(driver="budget_predictability", weight=4),
                    DriverWeightResponse(driver="implementation_complexity", weight=1),
                    DriverWeightResponse(driver="price_affordability", weight=1),
                ],
                price_sensitivity=0.6,
                switching_cost=0.2,
                alternatives=["in-house"],
                churn_threshold=-0.17,
                retention_threshold=0.04,
                adoption_friction=0.18,
                value_perception_explanation="explanation",
                segment_weight=2,
            ),
        ],
        scenarios=[
            GeneratedScenarioResponse(
                title="Raise price",
                scenario_type="pricing_increase",
                description="desc",
                input_parameters=ScenarioInputParametersResponse(price_change_percent=12, current_price_estimate=100),
            ),
            GeneratedScenarioResponse(
                title="Add premium forecasting",
                scenario_type="premium_feature_addition",
                description="desc",
                input_parameters=ScenarioInputParametersResponse(premium_feature="forecasting", price_change_percent=8),
            ),
            GeneratedScenarioResponse(
                title="Remove export",
                scenario_type="feature_removal",
                description="desc",
                input_parameters=ScenarioInputParametersResponse(removed_feature="csv export", feature_importance=0.8),
            ),
        ],
    )

    icps, scenarios = service._normalize_analysis_artifacts(payload)

    assert len(icps) == 3
    assert sum(icp.segment_weight for icp in icps) == pytest.approx(1.0, abs=0.001)
    assert sum(icps[0].driver_weights.values()) == pytest.approx(1.0, abs=0.001)
    assert icps[0].price_sensitivity == 1.0
    assert icps[0].switching_cost == 0.0
    assert scenarios[0].input_parameters["price_change_percent"] == 12.0


def test_normalize_analysis_artifacts_rejects_missing_required_scenario_field() -> None:
    service = OpenAIAnalysisService()
    payload = AnalysisArtifactsResponse(
        icps=[
            GeneratedICPResponse(
                name="ICP 1",
                description="desc",
                use_case="use case",
                goals=["goal 1", "goal 2"],
                pain_points=["pain 1", "pain 2"],
                decision_drivers=["price_affordability", "automation_coverage", "analytics_depth"],
                driver_weights=[
                    DriverWeightResponse(driver="price_affordability", weight=1),
                    DriverWeightResponse(driver="automation_coverage", weight=1),
                    DriverWeightResponse(driver="analytics_depth", weight=1),
                ],
                price_sensitivity=0.7,
                switching_cost=0.2,
                alternatives=["manual"],
                churn_threshold=-0.2,
                retention_threshold=0.05,
                adoption_friction=0.2,
                value_perception_explanation="explanation",
                segment_weight=1,
            ),
            GeneratedICPResponse(
                name="ICP 2",
                description="desc",
                use_case="use case",
                goals=["goal 1", "goal 2"],
                pain_points=["pain 1", "pain 2"],
                decision_drivers=["team_enablement", "support_reliability", "feature_completeness"],
                driver_weights=[
                    DriverWeightResponse(driver="team_enablement", weight=1),
                    DriverWeightResponse(driver="support_reliability", weight=1),
                    DriverWeightResponse(driver="feature_completeness", weight=1),
                ],
                price_sensitivity=0.4,
                switching_cost=0.3,
                alternatives=["competitor"],
                churn_threshold=-0.2,
                retention_threshold=0.05,
                adoption_friction=0.2,
                value_perception_explanation="explanation",
                segment_weight=1,
            ),
            GeneratedICPResponse(
                name="ICP 3",
                description="desc",
                use_case="use case",
                goals=["goal 1", "goal 2"],
                pain_points=["pain 1", "pain 2"],
                decision_drivers=["budget_predictability", "implementation_complexity", "price_affordability"],
                driver_weights=[
                    DriverWeightResponse(driver="budget_predictability", weight=1),
                    DriverWeightResponse(driver="implementation_complexity", weight=1),
                    DriverWeightResponse(driver="price_affordability", weight=1),
                ],
                price_sensitivity=0.6,
                switching_cost=0.2,
                alternatives=["in-house"],
                churn_threshold=-0.17,
                retention_threshold=0.04,
                adoption_friction=0.18,
                value_perception_explanation="explanation",
                segment_weight=1,
            ),
        ],
        scenarios=[
            GeneratedScenarioResponse(
                title="Raise price",
                scenario_type="pricing_increase",
                description="desc",
                input_parameters=ScenarioInputParametersResponse(current_price_estimate=100),
            ),
            GeneratedScenarioResponse(
                title="Add premium forecasting",
                scenario_type="premium_feature_addition",
                description="desc",
                input_parameters=ScenarioInputParametersResponse(premium_feature="forecasting"),
            ),
            GeneratedScenarioResponse(
                title="Remove export",
                scenario_type="feature_removal",
                description="desc",
                input_parameters=ScenarioInputParametersResponse(removed_feature="csv export", feature_importance=0.8),
            ),
        ],
    )

    with pytest.raises(AppException):
        service._normalize_analysis_artifacts(payload)


def test_openai_response_schemas_avoid_dynamic_object_maps() -> None:
    from openai.lib._pydantic import to_strict_json_schema

    product_schema = to_strict_json_schema(ProductUnderstandingResponse)
    confidence_schema = product_schema["$defs"]["ConfidenceScoresResponse"]
    customer_logic_schema = product_schema["$defs"]["ProductCustomerLogicResponse"]
    feature_cluster_schema = product_schema["$defs"]["ProductFeatureClusterResponse"]
    assert confidence_schema["additionalProperties"] is False
    assert customer_logic_schema["additionalProperties"] is False
    assert feature_cluster_schema["additionalProperties"] is False

    artifact_schema = to_strict_json_schema(AnalysisArtifactsResponse)
    icp_schema = artifact_schema["$defs"]["GeneratedICPResponse"]
    scenario_schema = artifact_schema["$defs"]["GeneratedScenarioResponse"]
    input_parameters_schema = artifact_schema["$defs"]["ScenarioInputParametersResponse"]

    assert icp_schema["properties"]["driver_weights"]["type"] == "array"
    assert scenario_schema["properties"]["input_parameters"]["$ref"] == "#/$defs/ScenarioInputParametersResponse"
    assert input_parameters_schema["additionalProperties"] is False


@pytest.mark.asyncio
async def test_call_with_retry_retries_on_parse_validation_error() -> None:
    class FakeResponses:
        def __init__(self) -> None:
            self.calls = 0
            self.max_output_tokens: list[int] = []

        async def parse(self, **kwargs):
            self.calls += 1
            self.max_output_tokens.append(kwargs["max_output_tokens"])
            if self.calls == 1:
                ProductUnderstandingResponse.model_validate_json('{"company_name"')

            payload = sample_product_payload()
            return SimpleNamespace(output_parsed=payload)

    class FakeClient:
        def __init__(self) -> None:
            self.responses = FakeResponses()

    client = FakeClient()
    service = OpenAIAnalysisService(client=client)

    understanding = await service.generate_product_understanding(sample_scrape_result(), user_identifier="test-user")

    assert understanding.company_name == "Acme"
    assert client.responses.calls == 2
    assert client.responses.max_output_tokens == [1600, 3200]
