from __future__ import annotations

from copy import deepcopy

from app.models.analysis import Analysis, AnalysisStatus
from app.models.extracted_product_data import ExtractedProductData
from app.models.icp_profile import ICPProfile
from app.models.scenario import Scenario
from app.models.simulation import SimulationResult, SimulationRun
from app.repositories.analysis_repository import AnalysisRepository
from app.services.analysis_workflow import clone_workflow_state


class AnalysisCloner:
    def __init__(self, repository: AnalysisRepository) -> None:
        self.repository = repository

    def clone(self, *, source: Analysis, target_user_id: str, input_url: str, normalized_url: str) -> Analysis:
        target = self.repository.create(
            user_id=target_user_id,
            input_url=input_url,
            normalized_url=normalized_url,
            status=AnalysisStatus.completed,
        )
        target.started_at = source.started_at
        target.completed_at = source.completed_at
        target.current_stage = source.current_stage
        target.workflow_state_json = clone_workflow_state(source.workflow_state_json)

        if source.extracted_product_data:
            product = source.extracted_product_data
            target.extracted_product_data = ExtractedProductData(
                company_name=product.company_name,
                product_name=product.product_name,
                category=product.category,
                subcategory=product.subcategory,
                positioning_summary=product.positioning_summary,
                pricing_model=product.pricing_model,
                monetization_hypothesis=product.monetization_hypothesis,
                raw_extracted_json=deepcopy(product.raw_extracted_json),
                normalized_json=deepcopy(product.normalized_json),
                confidence_score=product.confidence_score,
                is_user_edited=product.is_user_edited,
                edited_at=product.edited_at,
            )

        icp_map: dict[str, ICPProfile] = {}
        for icp in source.icp_profiles:
            cloned_icp = ICPProfile(
                name=icp.name,
                description=icp.description,
                use_case=icp.use_case,
                goals_json=deepcopy(icp.goals_json),
                pain_points_json=deepcopy(icp.pain_points_json),
                decision_drivers_json=deepcopy(icp.decision_drivers_json),
                driver_weights_json=deepcopy(icp.driver_weights_json),
                price_sensitivity=icp.price_sensitivity,
                switching_cost=icp.switching_cost,
                alternatives_json=deepcopy(icp.alternatives_json),
                churn_threshold=icp.churn_threshold,
                retention_threshold=icp.retention_threshold,
                adoption_friction=icp.adoption_friction,
                value_perception_explanation=icp.value_perception_explanation,
                segment_weight=icp.segment_weight,
                display_order=icp.display_order,
                is_user_edited=icp.is_user_edited,
                edited_at=icp.edited_at,
            )
            target.icp_profiles.append(cloned_icp)
            icp_map[icp.id] = cloned_icp

        scenario_map: dict[str, Scenario] = {}
        for scenario in source.scenarios:
            cloned_scenario = Scenario(
                title=scenario.title,
                scenario_type=scenario.scenario_type,
                description=scenario.description,
                input_parameters_json=deepcopy(scenario.input_parameters_json),
                display_order=scenario.display_order,
                is_user_edited=scenario.is_user_edited,
                edited_at=scenario.edited_at,
            )
            target.scenarios.append(cloned_scenario)
            scenario_map[scenario.id] = cloned_scenario

        for run in source.simulation_runs:
            cloned_run = SimulationRun(
                scenario=scenario_map[run.scenario_id],
                run_version=run.run_version,
                engine_version=run.engine_version,
                assumptions_json=deepcopy(run.assumptions_json),
            )
            target.simulation_runs.append(cloned_run)
            for result in run.results:
                cloned_run.results.append(
                    SimulationResult(
                        icp_profile=icp_map[result.icp_profile_id],
                        reaction=result.reaction,
                        utility_score_before=result.utility_score_before,
                        utility_score_after=result.utility_score_after,
                        delta_score=result.delta_score,
                        revenue_delta=result.revenue_delta,
                        perception_shift=result.perception_shift,
                        second_order_effects_json=deepcopy(result.second_order_effects_json),
                        driver_impacts_json=deepcopy(result.driver_impacts_json),
                        explanation=result.explanation,
                    )
                )
        self.repository.session.flush()
        return target
