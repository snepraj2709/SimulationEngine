from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.services.domain_types import SimulationComputationResult
from app.services.outcome_aggregator import OutcomeAggregator
from app.services.presenters import build_simulation_run_response
from app.tests.factories import sample_generated_icps, sample_generated_scenarios, sample_product_understanding


def test_outcome_aggregator_uses_baseline_revenue_per_account_for_percentage() -> None:
    icp = sample_generated_icps()[0].model_copy(update={"segment_weight": 1.0})
    result = SimulationComputationResult(
        reaction="retain",
        utility_score_before=0.6,
        utility_score_after=0.7,
        delta_score=0.1,
        revenue_delta=800.0,
        perception_shift=0.2,
        second_order_effects=[],
        driver_impacts={},
        explanation="test",
        assumptions={"baseline_revenue_per_account": 1200.0},
    )

    summary = OutcomeAggregator().aggregate(
        scenario_id="scenario-1",
        scenario_title="Test scenario",
        icps=[icp],
        results=[result],
    )

    assert summary.projected_retention_pct == 100.0
    assert summary.estimated_revenue_delta_pct == pytest.approx(0.67)
    assert summary.weighted_revenue_delta == 800.0


def test_build_simulation_run_response_rebuilds_summary_with_current_revenue_formula() -> None:
    now = datetime.now(UTC)
    understanding = sample_product_understanding()
    icp = sample_generated_icps()[0].model_copy(update={"segment_weight": 1.0})
    scenario_payload = sample_generated_scenarios()[0]

    profile = SimpleNamespace(
        id="icp-1",
        analysis_id="analysis-1",
        name=icp.name,
        description=icp.description,
        use_case=icp.use_case,
        goals_json=icp.goals,
        pain_points_json=icp.pain_points,
        decision_drivers_json=icp.decision_drivers,
        driver_weights_json=icp.driver_weights,
        price_sensitivity=icp.price_sensitivity,
        switching_cost=icp.switching_cost,
        alternatives_json=icp.alternatives,
        churn_threshold=icp.churn_threshold,
        retention_threshold=icp.retention_threshold,
        adoption_friction=icp.adoption_friction,
        value_perception_explanation=icp.value_perception_explanation,
        segment_weight=icp.segment_weight,
    )
    scenario = SimpleNamespace(
        id="scenario-1",
        analysis_id="analysis-1",
        title=scenario_payload.title,
        scenario_type=scenario_payload.scenario_type,
        description=scenario_payload.description,
        input_parameters_json=scenario_payload.input_parameters,
        created_at=now,
        updated_at=now,
    )
    result = SimpleNamespace(
        id="result-1",
        simulation_run_id="run-1",
        icp_profile_id="icp-1",
        reaction="retain",
        utility_score_before=0.6,
        utility_score_after=0.7,
        delta_score=0.1,
        revenue_delta=800.0,
        perception_shift=0.2,
        second_order_effects_json=[],
        driver_impacts_json={},
        explanation="test",
        created_at=now,
    )
    run = SimpleNamespace(
        id="run-1",
        analysis_id="analysis-1",
        scenario_id="scenario-1",
        run_version="1",
        engine_version="utility-v1",
        assumptions_json={
            "summary": {
                "projected_retention_pct": 100.0,
                "projected_downgrade_pct": 0.0,
                "projected_upgrade_pct": 0.0,
                "projected_churn_pct": 0.0,
                "estimated_revenue_delta_pct": 800.0,
                "weighted_revenue_delta": 800.0,
                "perception_shift_score": 0.2,
                "perception_shift_label": "positive",
                "highest_risk_icps": [profile.name],
                "top_negative_drivers": [],
                "top_positive_drivers": [],
                "second_order_effects": [],
            }
        },
        created_at=now,
        results=[result],
    )
    analysis = SimpleNamespace(
        scenarios=[scenario],
        icp_profiles=[profile],
        extracted_product_data=SimpleNamespace(normalized_json=understanding.normalized_json),
    )

    response = build_simulation_run_response(run, analysis)

    assert response.summary.estimated_revenue_delta_pct == pytest.approx(0.67)
    assert response.summary.weighted_revenue_delta == 800.0
