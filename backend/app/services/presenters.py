from __future__ import annotations

from app.models.analysis import Analysis
from app.models.icp_profile import ICPProfile
from app.models.simulation import SimulationRun
from app.schemas.analysis import AnalysisCreateResponse, AnalysisDetailResponse, AnalysisListItemResponse
from app.schemas.product import ExtractedProductDataResponse
from app.schemas.simulation import (
    ICPProfileResponse,
    ScenarioResponse,
    ScenarioSimulationSummary,
    SimulationResultResponse,
    SimulationRunResponse,
)
from app.services.domain_types import GeneratedICP, GeneratedScenario, SimulationComputationResult
from app.services.outcome_aggregator import OutcomeAggregator
from app.services.product_understanding_service import ProductUnderstandingService
from app.services.simulation_engine import SimulationEngine


def build_analysis_list_item(analysis: Analysis) -> AnalysisListItemResponse:
    return AnalysisListItemResponse.model_validate(analysis)


def build_analysis_create_response(
    analysis: Analysis,
    *,
    reused: bool = False,
    cloned_from_analysis_id: str | None = None,
) -> AnalysisCreateResponse:
    return AnalysisCreateResponse(
        analysis=build_analysis_list_item(analysis),
        reused=reused,
        cloned_from_analysis_id=cloned_from_analysis_id,
    )


def build_analysis_detail_response(analysis: Analysis) -> AnalysisDetailResponse:
    return AnalysisDetailResponse(
        id=analysis.id,
        input_url=analysis.input_url,
        normalized_url=analysis.normalized_url,
        status=str(analysis.status),
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        extracted_product_data=ExtractedProductDataResponse.model_validate(analysis.extracted_product_data)
        if analysis.extracted_product_data
        else None,
        icp_profiles=[ICPProfileResponse.model_validate(profile) for profile in analysis.icp_profiles],
        scenarios=[ScenarioResponse.model_validate(scenario) for scenario in analysis.scenarios],
        simulation_runs=[build_simulation_run_response(run, analysis) for run in analysis.simulation_runs],
    )


def build_simulation_run_response(run: SimulationRun, analysis: Analysis) -> SimulationRunResponse:
    summary = _rebuild_summary(run, analysis)
    return SimulationRunResponse(
        id=run.id,
        analysis_id=run.analysis_id,
        scenario_id=run.scenario_id,
        run_version=run.run_version,
        engine_version=run.engine_version,
        assumptions_json=run.assumptions_json,
        created_at=run.created_at,
        results=[SimulationResultResponse.model_validate(result) for result in run.results],
        summary=summary,
    )


def _rebuild_summary(run: SimulationRun, analysis: Analysis) -> ScenarioSimulationSummary:
    scenario_lookup = {scenario.id: scenario for scenario in analysis.scenarios}
    scenario_entity = scenario_lookup[run.scenario_id]
    icps = [generated_icp_from_entity(profile) for profile in analysis.icp_profiles]
    result_map = {result.icp_profile_id: result for result in run.results}
    baseline_revenue_per_account: float | None = None
    if analysis.extracted_product_data is not None:
        understanding = ProductUnderstandingService().build_from_normalized(analysis.extracted_product_data.normalized_json)
        scenario = GeneratedScenario(
            title=scenario_entity.title,
            scenario_type=str(scenario_entity.scenario_type),
            description=scenario_entity.description,
            input_parameters=dict(scenario_entity.input_parameters_json),
        )
        baseline_revenue_per_account = SimulationEngine().baseline_revenue_for_scenario(
            understanding=understanding,
            scenario=scenario,
        )
    ordered_results = [
        SimulationComputationResult(
            reaction=result_map[profile.id].reaction,
            utility_score_before=result_map[profile.id].utility_score_before,
            utility_score_after=result_map[profile.id].utility_score_after,
            delta_score=result_map[profile.id].delta_score,
            revenue_delta=result_map[profile.id].revenue_delta,
            perception_shift=result_map[profile.id].perception_shift,
            second_order_effects=list(result_map[profile.id].second_order_effects_json),
            driver_impacts=dict(result_map[profile.id].driver_impacts_json),
            explanation=result_map[profile.id].explanation,
            assumptions={"baseline_revenue_per_account": baseline_revenue_per_account}
            if baseline_revenue_per_account is not None
            else {},
        )
        for profile in analysis.icp_profiles
    ]
    summary = OutcomeAggregator().aggregate(
        scenario_id=run.scenario_id,
        scenario_title=scenario_entity.title,
        icps=icps,
        results=ordered_results,
    )
    return ScenarioSimulationSummary(
        scenario_id=run.scenario_id,
        scenario_title=scenario_entity.title,
        **summary.model_dump(),
    )


def generated_icp_from_entity(profile: ICPProfile) -> GeneratedICP:
    return GeneratedICP(
        name=profile.name,
        description=profile.description,
        use_case=profile.use_case,
        goals=list(profile.goals_json),
        pain_points=list(profile.pain_points_json),
        decision_drivers=list(profile.decision_drivers_json),
        driver_weights=dict(profile.driver_weights_json),
        price_sensitivity=profile.price_sensitivity,
        switching_cost=profile.switching_cost,
        alternatives=list(profile.alternatives_json),
        churn_threshold=profile.churn_threshold,
        retention_threshold=profile.retention_threshold,
        adoption_friction=profile.adoption_friction,
        value_perception_explanation=profile.value_perception_explanation,
        segment_weight=profile.segment_weight,
    )
