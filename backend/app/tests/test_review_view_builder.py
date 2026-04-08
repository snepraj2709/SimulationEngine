from pydantic import ValidationError
import pytest

from app.models.analysis import Analysis, AnalysisStatus
from app.models.extracted_product_data import ExtractedProductData
from app.models.icp_profile import ICPProfile
from app.models.scenario import Scenario, ScenarioType
from app.schemas.simulation import BehavioralSignalResponse
from app.services.review_view_builder import build_icp_view_model, build_scenario_review_views
from app.tests.factories import sample_generated_icps, sample_generated_scenarios, sample_product_understanding


def _build_icp_model(index: int = 0) -> ICPProfile:
    sample = sample_generated_icps()[index]
    return ICPProfile(
        analysis_id="analysis-1",
        display_order=index,
        name=sample.name,
        description=sample.description,
        use_case=sample.use_case,
        goals_json=sample.goals,
        pain_points_json=sample.pain_points,
        decision_drivers_json=sample.decision_drivers,
        driver_weights_json=sample.driver_weights,
        price_sensitivity=sample.price_sensitivity,
        switching_cost=sample.switching_cost,
        alternatives_json=sample.alternatives,
        churn_threshold=sample.churn_threshold,
        retention_threshold=sample.retention_threshold,
        adoption_friction=sample.adoption_friction,
        value_perception_explanation=sample.value_perception_explanation,
        segment_weight=sample.segment_weight,
        is_user_edited=False,
    )


def _build_scenario_model(index: int = 0) -> Scenario:
    sample = sample_generated_scenarios()[index]
    return Scenario(
        analysis_id="analysis-1",
        display_order=index,
        title=sample.title,
        scenario_type=ScenarioType(sample.scenario_type),
        description=sample.description,
        input_parameters_json=sample.input_parameters,
        is_user_edited=False,
    )


def _build_analysis() -> Analysis:
    understanding = sample_product_understanding()
    analysis = Analysis(
        user_id="user-1",
        input_url="https://acme.example/",
        normalized_url="https://acme.example/",
        status=AnalysisStatus.awaiting_review,
        current_stage="scenarios",
        workflow_state_json={},
    )
    analysis.extracted_product_data = ExtractedProductData(
        analysis_id="analysis-1",
        company_name=understanding.company_name,
        product_name=understanding.product_name,
        category=understanding.category,
        subcategory=understanding.subcategory,
        positioning_summary=understanding.positioning_summary,
        pricing_model=understanding.pricing_model,
        monetization_hypothesis=understanding.monetization_hypothesis,
        raw_extracted_json=understanding.raw_extracted_json,
        normalized_json=understanding.normalized_json,
        confidence_score=understanding.confidence_score,
        is_user_edited=False,
    )
    analysis.icp_profiles = [_build_icp_model(index) for index in range(3)]
    analysis.scenarios = [_build_scenario_model(index) for index in range(3)]
    analysis.simulation_runs = []
    return analysis


def test_behavioral_signal_response_rejects_out_of_range_values() -> None:
    with pytest.raises(ValidationError):
        BehavioralSignalResponse(
            signal_key="priceSensitivity",
            label="Price Sensitivity",
            value_1_to_5=6,
            editable=True,
        )


def test_build_icp_view_model_normalizes_compact_signals() -> None:
    view_model = build_icp_view_model(_build_icp_model(), understanding=sample_product_understanding())

    assert view_model.segment_name == "Revenue operations lead"
    assert view_model.confidence is not None
    assert [signal.signal_key for signal in view_model.behavioral_signals] == [
        "priceSensitivity",
        "switchingFriction",
        "timeToValueExpectation",
        "proofRequirement",
        "implementationTolerance",
        "retentionStability",
    ]
    assert all(1 <= signal.value_1_to_5 <= 5 for signal in view_model.behavioral_signals)
    assert next(signal for signal in view_model.behavioral_signals if signal.signal_key == "timeToValueExpectation").editable is False
    assert view_model.editable_fields[-1].field == "decisionDrivers"


def test_build_scenario_review_views_formats_expected_impact_and_recommendations() -> None:
    review_views = build_scenario_review_views(_build_analysis())

    assert len(review_views) == 3
    recommendation_ranks = sorted(view.recommendation.priority_rank for view in review_views.values())
    assert recommendation_ranks == [1, 2, 3]

    first_view = next(iter(review_views.values()))
    assert first_view.linked_icp_summary is not None
    assert first_view.expected_impact[0].metric_key == "revenue"
    assert {impact.metric_key for impact in first_view.expected_impact} == {
        "revenue",
        "conversion",
        "churn_risk",
        "activation_speed",
    }
    assert first_view.metadata.scenario_tags
    assert first_view.recommendation.recommendation_label
    assert first_view.why_this_might_work
    assert first_view.tradeoffs
