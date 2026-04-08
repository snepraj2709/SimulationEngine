from __future__ import annotations

from datetime import datetime

from app.models.analysis import Analysis
from app.models.icp_profile import ICPProfile
from app.models.scenario import Scenario, ScenarioType
from app.models.simulation import SimulationRun
from app.schemas.analysis import (
    AnalysisCreateResponse,
    AnalysisDetailResponse,
    AnalysisListItemResponse,
    AnalysisWorkflowResponse,
    WorkflowStepResponse,
)
from app.schemas.product import ExtractedProductDataResponse
from app.schemas.simulation import (
    ICPProfileResponse,
    ScenarioResponse,
    ScenarioInputFieldResponse,
    ScenarioInputSchemaResponse,
    ScenarioSimulationSummary,
    SimulationResultResponse,
    SimulationRunResponse,
)
from app.services.analysis_workflow import WORKFLOW_STAGE_LABELS, WORKFLOW_STAGES, ensure_workflow_state, final_review_workflow_state, next_stage
from app.services.domain_types import GeneratedICP, GeneratedScenario, SimulationComputationResult
from app.services.outcome_aggregator import OutcomeAggregator
from app.services.product_understanding_service import ProductUnderstandingService
from app.services.review_view_builder import build_icp_view_model, build_scenario_review_views
from app.services.simulation_engine import SimulationEngine


def build_analysis_list_item(analysis: Analysis) -> AnalysisListItemResponse:
    return AnalysisListItemResponse(
        id=analysis.id,
        input_url=analysis.input_url,
        normalized_url=analysis.normalized_url,
        status=str(analysis.status),
        current_stage=_analysis_current_stage(analysis),  # type: ignore[arg-type]
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message,
    )


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
    current_stage = _analysis_current_stage(analysis)
    understanding = (
        ProductUnderstandingService().build_from_normalized(analysis.extracted_product_data.normalized_json)
        if analysis.extracted_product_data
        else None
    )
    ordered_profiles = sorted(analysis.icp_profiles, key=_ordered_entity_key)
    icp_view_models = {
        profile.id: build_icp_view_model(profile, understanding=understanding)
        for profile in ordered_profiles
    }
    scenario_review_views = build_scenario_review_views(analysis)
    return AnalysisDetailResponse(
        id=analysis.id,
        input_url=analysis.input_url,
        normalized_url=analysis.normalized_url,
        status=str(analysis.status),
        current_stage=current_stage,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        workflow=build_analysis_workflow_response(analysis, current_stage=current_stage),
        extracted_product_data=ExtractedProductDataResponse.model_validate(analysis.extracted_product_data)
        if analysis.extracted_product_data
        else None,
        icp_profiles=[
            ICPProfileResponse.model_validate(profile).model_copy(update={"view_model": icp_view_models.get(profile.id)})
            for profile in ordered_profiles
        ],
        scenarios=[
            build_scenario_response(scenario, review_view=scenario_review_views.get(scenario.id))
            for scenario in sorted(analysis.scenarios, key=_ordered_entity_key)
        ],
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
    ordered_profiles = sorted(analysis.icp_profiles, key=_ordered_entity_key)
    icps = [generated_icp_from_entity(profile) for profile in ordered_profiles]
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
        for profile in ordered_profiles
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


def build_analysis_workflow_response(analysis: Analysis, *, current_stage: str | None = None) -> AnalysisWorkflowResponse:
    stage = current_stage or _analysis_current_stage(analysis)
    state = _analysis_workflow_state(analysis)
    steps = [
        WorkflowStepResponse(
            stage=workflow_stage,
            label=WORKFLOW_STAGE_LABELS[workflow_stage],
            status=str(state[workflow_stage]["status"]),
            is_current=workflow_stage == stage,
            is_complete=str(state[workflow_stage]["status"]) == "completed",
            started_at=_parse_workflow_datetime(state[workflow_stage]["started_at"]),
            completed_at=_parse_workflow_datetime(state[workflow_stage]["completed_at"]),
            edited=bool(state[workflow_stage]["edited"]),
            error_message=state[workflow_stage]["error_message"],
        )
        for workflow_stage in WORKFLOW_STAGES
    ]
    return AnalysisWorkflowResponse(
        current_stage=stage,
        next_stage=next_stage(stage),  # type: ignore[arg-type]
        steps=steps,
        available_actions=_available_actions_for(stage, str(analysis.status)),
    )


def build_scenario_response(
    scenario: Scenario,
    *,
    review_view=None,
) -> ScenarioResponse:
    return ScenarioResponse(
        id=scenario.id,
        analysis_id=scenario.analysis_id,
        display_order=scenario.display_order,
        is_user_edited=scenario.is_user_edited,
        edited_at=scenario.edited_at,
        title=scenario.title,
        scenario_type=str(scenario.scenario_type),
        description=scenario.description,
        input_parameters_json=dict(scenario.input_parameters_json),
        input_parameters_schema=build_scenario_input_schema(str(scenario.scenario_type)),
        created_at=scenario.created_at,
        updated_at=scenario.updated_at,
        review_view=review_view,
    )


def build_scenario_input_schema(scenario_type: str) -> ScenarioInputSchemaResponse:
    fields: list[ScenarioInputFieldResponse] = []
    if scenario_type in {ScenarioType.pricing_increase.value, ScenarioType.pricing_decrease.value}:
        fields.append(
            ScenarioInputFieldResponse(
                key="price_change_percent",
                label="Price change (%)",
                input_type="number",
                required=True,
                minimum=0.1,
                maximum=50.0,
                step=0.1,
                helper_text="Use a positive percentage. The backend handles increase vs decrease by scenario type.",
            )
        )
    if scenario_type == ScenarioType.feature_removal.value:
        fields.extend(
            [
                ScenarioInputFieldResponse(
                    key="removed_feature",
                    label="Removed feature",
                    input_type="text",
                    required=True,
                ),
                ScenarioInputFieldResponse(
                    key="feature_importance",
                    label="Feature importance",
                    input_type="number",
                    required=True,
                    minimum=0.05,
                    maximum=1.0,
                    step=0.01,
                ),
            ]
        )
    if scenario_type == ScenarioType.premium_feature_addition.value:
        fields.extend(
            [
                ScenarioInputFieldResponse(
                    key="premium_feature",
                    label="Premium feature",
                    input_type="text",
                    required=True,
                ),
                ScenarioInputFieldResponse(
                    key="price_change_percent",
                    label="Price change (%)",
                    input_type="number",
                    required=False,
                    minimum=0.0,
                    maximum=50.0,
                    step=0.1,
                ),
            ]
        )
    if scenario_type == ScenarioType.bundling.value:
        fields.extend(
            [
                ScenarioInputFieldResponse(
                    key="bundle_name",
                    label="Bundle name",
                    input_type="text",
                    required=True,
                ),
                ScenarioInputFieldResponse(
                    key="bundle_price_change_percent",
                    label="Bundle price change (%)",
                    input_type="number",
                    required=False,
                    minimum=0.0,
                    maximum=50.0,
                    step=0.1,
                ),
            ]
        )
    if scenario_type == ScenarioType.unbundling.value:
        fields.extend(
            [
                ScenarioInputFieldResponse(
                    key="service_name",
                    label="Service name",
                    input_type="text",
                    required=True,
                ),
                ScenarioInputFieldResponse(
                    key="price_change_percent",
                    label="Price change (%)",
                    input_type="number",
                    required=False,
                    minimum=0.0,
                    maximum=50.0,
                    step=0.1,
                ),
            ]
        )

    fields.extend(
        [
            ScenarioInputFieldResponse(
                key="current_price_estimate",
                label="Current price estimate",
                input_type="number",
                required=False,
                minimum=1.0,
                maximum=100000.0,
                step=1.0,
            ),
            ScenarioInputFieldResponse(
                key="market",
                label="Market",
                input_type="text",
                required=False,
            ),
            ScenarioInputFieldResponse(
                key="plan_tier",
                label="Plan tier",
                input_type="text",
                required=False,
            ),
            ScenarioInputFieldResponse(
                key="billing_period",
                label="Billing period",
                input_type="text",
                required=False,
            ),
        ]
    )
    return ScenarioInputSchemaResponse(fields=fields)


def _analysis_current_stage(analysis: Analysis) -> str:
    if getattr(analysis, "current_stage", None):
        return str(analysis.current_stage)
    if str(analysis.status) == "completed":
        return "final_review"
    return "product_understanding"


def _analysis_workflow_state(analysis: Analysis) -> dict:
    raw_state = getattr(analysis, "workflow_state_json", None)
    if raw_state:
        return ensure_workflow_state(raw_state)
    if str(analysis.status) == "completed":
        return final_review_workflow_state()
    return ensure_workflow_state({})


def _parse_workflow_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _available_actions_for(stage: str, status: str) -> list[str]:
    if status in {"queued", "processing"}:
        return []
    if stage == "product_understanding":
        return ["edit", "proceed"]
    if stage == "icp_profiles":
        return ["edit", "proceed", "reopen"]
    if stage == "scenarios":
        return ["edit", "proceed", "reopen"]
    if stage == "decision_flow":
        return ["simulate", "reopen"]
    if stage == "final_review":
        return ["simulate", "soft_refresh", "compare", "feedback"]
    return []


def _ordered_entity_key(item) -> tuple[int, datetime | None]:
    return (int(getattr(item, "display_order", 0) or 0), getattr(item, "created_at", None))
