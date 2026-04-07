from types import SimpleNamespace

import pytest

from app.core.exceptions import AppException
from app.services.llm.openai_analysis_service import (
    AnalysisArtifactsResponse,
    ConfidenceScoresResponse,
    DriverWeightResponse,
    GeneratedICPResponse,
    GeneratedScenarioResponse,
    OpenAIAnalysisService,
    ProductUnderstandingResponse,
    ScenarioInputParametersResponse,
)
from app.tests.factories import sample_scrape_result


def test_normalize_product_understanding_builds_normalized_payload() -> None:
    service = OpenAIAnalysisService()
    payload = ProductUnderstandingResponse(
        company_name="Acme",
        product_name="Acme Growth Platform",
        category="B2B Software",
        subcategory="Revenue Operations",
        positioning_summary="Acme helps revenue teams automate onboarding and renewal workflows.",
        pricing_model="sales_led_custom_pricing",
        feature_clusters=["workflow automation", "renewal analytics", "workflow automation"],
        monetization_hypothesis="Annual contracts from revenue teams.",
        target_customer_signals=["revenue teams", "customer success leaders"],
        confidence_score=0.88,
        confidence_scores=ConfidenceScoresResponse(
            company_name=0.9,
            category=0.84,
            pricing_model=0.88,
            feature_clusters=0.88,
            target_customer_signals=0.88,
            positioning_summary=0.88,
        ),
        warnings=["Public pricing is limited."],
    )

    understanding = service._normalize_product_understanding(payload, sample_scrape_result())

    assert understanding.company_name == "Acme"
    assert understanding.normalized_json["company_name"] == "Acme"
    assert understanding.feature_clusters == ["workflow automation", "renewal analytics"]
    assert understanding.confidence_scores["pricing_model"] == pytest.approx(0.88)


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
    assert confidence_schema["additionalProperties"] is False

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

            payload = ProductUnderstandingResponse(
                company_name="Acme",
                product_name="Acme Growth Platform",
                category="B2B Software",
                subcategory="Revenue Operations",
                positioning_summary="Acme helps revenue teams automate onboarding and renewal workflows.",
                pricing_model="sales_led_custom_pricing",
                feature_clusters=["workflow automation", "renewal analytics"],
                monetization_hypothesis="Annual contracts from revenue teams.",
                target_customer_signals=["revenue teams", "customer success leaders"],
                confidence_score=0.88,
                confidence_scores=ConfidenceScoresResponse(
                    company_name=0.9,
                    category=0.84,
                    pricing_model=0.88,
                    feature_clusters=0.88,
                    target_customer_signals=0.88,
                    positioning_summary=0.88,
                ),
                warnings=[],
            )
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
