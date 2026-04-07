from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.analysis import Analysis, AnalysisStatus
from app.models.extracted_product_data import ExtractedProductData
from app.models.feedback import FeedbackEvent
from app.models.icp_profile import ICPProfile
from app.models.scenario import Scenario
from app.models.simulation import SimulationResult, SimulationRun
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import WorkflowStage
from app.schemas.product import ProductUnderstandingUpdateRequest
from app.schemas.simulation import ICPProfileUpdateRequest, ScenarioUpdateRequest
from app.services.analysis_workflow import (
    ensure_workflow_state,
    mark_awaiting_review,
    mark_completed,
    mark_downstream_stale,
    mark_edited,
    mark_failed,
    mark_processing,
)
from app.services.domain_types import GeneratedICP, GeneratedScenario
from app.services.llm.openai_analysis_service import OpenAIAnalysisService
from app.services.outcome_aggregator import OutcomeAggregator
from app.services.product_understanding_service import ProductUnderstandingService
from app.services.scraper_service import ScraperService
from app.services.simulation_engine import SimulationEngine

logger = get_logger(__name__)


class AnalysisPipelineService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AnalysisRepository(session)
        self.scraper = ScraperService()
        self.llm_analysis = OpenAIAnalysisService()
        self.product_understanding = ProductUnderstandingService()
        self.simulation_engine = SimulationEngine()
        self.outcome_aggregator = OutcomeAggregator()

    async def process_analysis(self, analysis_id: str) -> None:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis is None:
            raise AppException(404, "analysis_not_found", "Analysis not found.")

        analysis.current_stage = "product_understanding"
        analysis.workflow_state_json = mark_processing(analysis.workflow_state_json, "product_understanding")
        self.repository.mark_processing(analysis)
        self.session.commit()

        try:
            scrape_result = await self.scraper.scrape(analysis.normalized_url)
            understanding = await self.llm_analysis.generate_product_understanding(
                scrape_result,
                user_identifier=analysis.user_id,
            )
            self._upsert_product_understanding(analysis, understanding, is_user_edited=False)
            analysis.workflow_state_json = mark_awaiting_review(
                analysis.workflow_state_json,
                "product_understanding",
                edited=False,
            )
            self.repository.mark_awaiting_review(analysis)
            self.session.commit()
            logger.info(
                "Product understanding generated",
                extra={"extra_data": {"analysis_id": analysis.id, "normalized_url": analysis.normalized_url}},
            )
        except AppException as exc:
            self.session.rollback()
            self._mark_failed(analysis_id, "product_understanding", exc.detail)
        except Exception as exc:  # pragma: no cover - safety net
            self.session.rollback()
            logger.exception("Unexpected analysis failure", extra={"extra_data": {"analysis_id": analysis_id}})
            self._mark_failed(analysis_id, "product_understanding", "Analysis pipeline failed unexpectedly.")
            raise exc

    async def advance_analysis(self, analysis_id: str, *, expected_stage: WorkflowStage) -> Analysis:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis is None:
            raise AppException(404, "analysis_not_found", "Analysis not found.")
        self._ensure_stage_ready(analysis, expected_stage)

        try:
            if expected_stage == "product_understanding":
                await self._generate_icps(analysis)
            elif expected_stage == "icp_profiles":
                await self._generate_scenarios(analysis)
            elif expected_stage == "scenarios":
                self._enter_decision_flow(analysis)
            else:
                raise AppException(409, "invalid_workflow_transition", "This stage cannot proceed automatically.")
        except AppException as exc:
            self.session.rollback()
            self._mark_failed(analysis_id, expected_stage, exc.detail)
            raise
        except Exception as exc:  # pragma: no cover - safety net
            self.session.rollback()
            logger.exception(
                "Unexpected analysis progression failure",
                extra={"extra_data": {"analysis_id": analysis_id, "stage": expected_stage}},
            )
            self._mark_failed(analysis_id, expected_stage, "Analysis progression failed unexpectedly.")
            raise exc

        refreshed = self.session.get(Analysis, analysis_id)
        assert refreshed is not None
        return refreshed

    def reopen_stage(self, *, analysis: Analysis, stage: WorkflowStage, entity_id: str | None = None) -> Analysis:
        self._validate_reopen_target(analysis=analysis, stage=stage, entity_id=entity_id)
        if stage == "product_understanding":
            self._clear_downstream_from_product(analysis)
        elif stage == "icp_profiles":
            self._clear_downstream_from_icps(analysis)
        elif stage == "scenarios":
            self._clear_downstream_from_scenarios(analysis)
        else:
            raise AppException(409, "invalid_reopen_stage", "This stage cannot be reopened.")

        analysis.current_stage = stage
        analysis.workflow_state_json = mark_awaiting_review(analysis.workflow_state_json, stage)
        analysis.workflow_state_json = mark_downstream_stale(analysis.workflow_state_json, stage)
        self.repository.mark_awaiting_review(analysis)
        analysis.completed_at = None
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def update_product_understanding(
        self,
        *,
        analysis: Analysis,
        payload: ProductUnderstandingUpdateRequest,
    ) -> Analysis:
        product = analysis.extracted_product_data
        if product is None:
            raise AppException(409, "analysis_incomplete", "Product understanding is not available yet.")

        current = self.product_understanding.build_from_normalized(product.normalized_json)
        updated = self.llm_analysis.normalize_product_understanding_update(payload, existing=current)
        self._upsert_product_understanding(analysis, updated, is_user_edited=True)
        analysis.current_stage = "product_understanding"
        analysis.workflow_state_json = mark_edited(analysis.workflow_state_json, "product_understanding")
        analysis.workflow_state_json = mark_downstream_stale(analysis.workflow_state_json, "product_understanding")
        self._clear_downstream_from_product(analysis)
        self.repository.mark_awaiting_review(analysis)
        analysis.completed_at = None
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def update_icp_profile(
        self,
        *,
        analysis: Analysis,
        icp_id: str,
        payload: ICPProfileUpdateRequest,
    ) -> Analysis:
        icp = next((item for item in analysis.icp_profiles if item.id == icp_id), None)
        if icp is None:
            raise AppException(404, "icp_not_found", "ICP profile not found for this analysis.")

        updated = self.llm_analysis.normalize_icp_update(payload)
        self._sync_icp_entity(icp, updated)
        icp.is_user_edited = True
        icp.edited_at = datetime.now(UTC)

        analysis.current_stage = "icp_profiles"
        analysis.workflow_state_json = mark_edited(analysis.workflow_state_json, "icp_profiles")
        analysis.workflow_state_json = mark_downstream_stale(analysis.workflow_state_json, "icp_profiles")
        self._clear_downstream_from_icps(analysis)
        self.repository.mark_awaiting_review(analysis)
        analysis.completed_at = None
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def update_scenario(
        self,
        *,
        analysis: Analysis,
        scenario_id: str,
        payload: ScenarioUpdateRequest,
    ) -> Analysis:
        scenario = next((item for item in analysis.scenarios if item.id == scenario_id), None)
        if scenario is None:
            raise AppException(404, "scenario_not_found", "Scenario not found for this analysis.")

        updated = self.llm_analysis.normalize_scenario_update(payload)
        self._sync_scenario_entity(scenario, updated)
        scenario.is_user_edited = True
        scenario.edited_at = datetime.now(UTC)

        analysis.current_stage = "scenarios"
        analysis.workflow_state_json = mark_edited(analysis.workflow_state_json, "scenarios")
        analysis.workflow_state_json = mark_downstream_stale(analysis.workflow_state_json, "scenarios")
        self._clear_downstream_from_scenarios(analysis)
        self.repository.mark_awaiting_review(analysis)
        analysis.completed_at = None
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    async def rerun_scenario(
        self,
        *,
        analysis: Analysis,
        scenario: Scenario,
        input_overrides: dict,
        run_version: str,
    ) -> SimulationRun:
        if analysis.current_stage not in {"decision_flow", "final_review"}:
            raise AppException(409, "analysis_not_ready", "Simulation is only available during decision flow or final review.")
        product = analysis.extracted_product_data
        if product is None:
            raise AppException(409, "analysis_incomplete", "Simulation cannot run without product understanding.")

        understanding = self.product_understanding.build_from_normalized(product.normalized_json)
        ordered_icp_entities = sorted(analysis.icp_profiles, key=lambda item: (item.display_order, item.created_at))
        generated_icps = [self._icp_from_entity(icp) for icp in ordered_icp_entities]
        generated_scenario = GeneratedScenario(
            title=scenario.title,
            scenario_type=str(scenario.scenario_type),
            description=scenario.description,
            input_parameters={**scenario.input_parameters_json, **input_overrides},
        )
        run = self._create_simulation_run(
            analysis,
            scenario,
            understanding,
            generated_icps,
            ordered_icp_entities,
            generated_scenario,
            run_version=run_version,
        )
        self.session.add(run)

        if analysis.current_stage == "decision_flow":
            analysis.workflow_state_json = mark_completed(analysis.workflow_state_json, "decision_flow")
            analysis.workflow_state_json = mark_completed(analysis.workflow_state_json, "final_review")
            analysis.current_stage = "final_review"
            self.repository.mark_completed(analysis)
        else:
            self.repository.mark_completed(analysis)

        self.session.commit()
        self.session.refresh(run)
        return run

    async def _generate_icps(self, analysis: Analysis) -> None:
        product = analysis.extracted_product_data
        if product is None:
            raise AppException(409, "analysis_incomplete", "Product understanding must be ready before generating ICPs.")

        analysis.workflow_state_json = mark_completed(analysis.workflow_state_json, "product_understanding")
        analysis.current_stage = "icp_profiles"
        analysis.workflow_state_json = mark_processing(analysis.workflow_state_json, "icp_profiles")
        self.repository.mark_processing(analysis)
        self.session.commit()

        understanding = self.product_understanding.build_from_normalized(product.normalized_json)
        generated_icps = await self.llm_analysis.generate_icps(understanding, user_identifier=analysis.user_id)
        self._clear_icps(analysis)
        for order, icp in enumerate(generated_icps):
            self._persist_icp(analysis, icp, display_order=order)
        self.session.flush()
        analysis.workflow_state_json = mark_awaiting_review(analysis.workflow_state_json, "icp_profiles")
        self.repository.mark_awaiting_review(analysis)
        self.session.commit()

    async def _generate_scenarios(self, analysis: Analysis) -> None:
        product = analysis.extracted_product_data
        if product is None:
            raise AppException(409, "analysis_incomplete", "Product understanding must be ready before generating scenarios.")
        if len(analysis.icp_profiles) < 3:
            raise AppException(409, "analysis_incomplete", "At least 3 ICP profiles are required before generating scenarios.")

        self._normalize_icp_segment_weights(analysis)
        analysis.workflow_state_json = mark_completed(analysis.workflow_state_json, "icp_profiles")
        analysis.current_stage = "scenarios"
        analysis.workflow_state_json = mark_processing(analysis.workflow_state_json, "scenarios")
        self.repository.mark_processing(analysis)
        self.session.commit()

        understanding = self.product_understanding.build_from_normalized(product.normalized_json)
        generated_icps = [
            self._icp_from_entity(icp)
            for icp in sorted(analysis.icp_profiles, key=lambda item: (item.display_order, item.created_at))
        ]
        generated_scenarios = await self.llm_analysis.generate_scenarios(
            understanding,
            generated_icps,
            user_identifier=analysis.user_id,
        )
        self._clear_scenarios(analysis)
        for order, scenario in enumerate(generated_scenarios):
            self._persist_scenario(analysis, scenario, display_order=order)
        self.session.flush()
        analysis.workflow_state_json = mark_awaiting_review(analysis.workflow_state_json, "scenarios")
        self.repository.mark_awaiting_review(analysis)
        self.session.commit()

    def _enter_decision_flow(self, analysis: Analysis) -> None:
        if len(analysis.scenarios) != 3:
            raise AppException(409, "analysis_incomplete", "Scenario review must be complete before decision flow.")
        analysis.workflow_state_json = mark_completed(analysis.workflow_state_json, "scenarios")
        analysis.current_stage = "decision_flow"
        analysis.workflow_state_json = mark_awaiting_review(analysis.workflow_state_json, "decision_flow")
        self.repository.mark_awaiting_review(analysis)
        self.session.commit()

    def _upsert_product_understanding(
        self,
        analysis: Analysis,
        understanding,
        *,
        is_user_edited: bool,
    ) -> None:
        product = analysis.extracted_product_data
        if product is None:
            product = ExtractedProductData()
            analysis.extracted_product_data = product

        product.company_name = understanding.company_name
        product.product_name = understanding.product_name
        product.category = understanding.category
        product.subcategory = understanding.subcategory
        product.positioning_summary = understanding.positioning_summary
        product.pricing_model = understanding.pricing_model
        product.monetization_hypothesis = understanding.monetization_hypothesis
        product.raw_extracted_json = understanding.raw_extracted_json
        product.normalized_json = understanding.normalized_json
        product.confidence_score = understanding.confidence_score
        product.is_user_edited = is_user_edited
        product.edited_at = datetime.now(UTC) if is_user_edited else None

    def _persist_icp(self, analysis: Analysis, generated: GeneratedICP, *, display_order: int) -> ICPProfile:
        entity = ICPProfile(
            name=generated.name,
            description=generated.description,
            use_case=generated.use_case,
            goals_json=generated.goals,
            pain_points_json=generated.pain_points,
            decision_drivers_json=generated.decision_drivers,
            driver_weights_json=generated.driver_weights,
            price_sensitivity=generated.price_sensitivity,
            switching_cost=generated.switching_cost,
            alternatives_json=generated.alternatives,
            churn_threshold=generated.churn_threshold,
            retention_threshold=generated.retention_threshold,
            adoption_friction=generated.adoption_friction,
            value_perception_explanation=generated.value_perception_explanation,
            segment_weight=generated.segment_weight,
            display_order=display_order,
            is_user_edited=False,
            edited_at=None,
        )
        analysis.icp_profiles.append(entity)
        return entity

    def _persist_scenario(self, analysis: Analysis, generated: GeneratedScenario, *, display_order: int) -> Scenario:
        entity = Scenario(
            title=generated.title,
            scenario_type=generated.scenario_type,
            description=generated.description,
            input_parameters_json=generated.input_parameters,
            display_order=display_order,
            is_user_edited=False,
            edited_at=None,
        )
        analysis.scenarios.append(entity)
        return entity

    def _create_simulation_run(
        self,
        analysis: Analysis,
        scenario_entity: Scenario,
        understanding,
        generated_icps: list[GeneratedICP],
        icp_entities: list[ICPProfile],
        generated_scenario: GeneratedScenario,
        *,
        run_version: str = "1",
    ) -> SimulationRun:
        results_payload = [
            self.simulation_engine.simulate(
                understanding=understanding,
                icp=generated_icp,
                scenario=generated_scenario,
            )
            for generated_icp in generated_icps
        ]
        summary = self.outcome_aggregator.aggregate(
            scenario_id=scenario_entity.id,
            scenario_title=scenario_entity.title,
            icps=generated_icps,
            results=results_payload,
        )
        run = SimulationRun(
            analysis=analysis,
            scenario=scenario_entity,
            run_version=run_version,
            engine_version=self.simulation_engine.ENGINE_VERSION,
            assumptions_json={
                "scenario_title": scenario_entity.title,
                "summary": summary.model_dump(),
                "generated_at": datetime.now(UTC).isoformat(),
                "formula": "utility_after - utility_before with threshold-based reaction classification",
            },
        )
        for result_payload, icp_entity in zip(results_payload, icp_entities, strict=True):
            run.results.append(
                SimulationResult(
                    icp_profile=icp_entity,
                    reaction=result_payload.reaction,
                    utility_score_before=result_payload.utility_score_before,
                    utility_score_after=result_payload.utility_score_after,
                    delta_score=result_payload.delta_score,
                    revenue_delta=result_payload.revenue_delta,
                    perception_shift=result_payload.perception_shift,
                    second_order_effects_json=result_payload.second_order_effects,
                    driver_impacts_json=result_payload.driver_impacts,
                    explanation=result_payload.explanation,
                )
            )
        self.session.add(run)
        return run

    def _mark_failed(self, analysis_id: str, stage: WorkflowStage, message: str) -> None:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis is None:
            return
        analysis.workflow_state_json = mark_failed(analysis.workflow_state_json, stage, message)
        self.repository.mark_failed(analysis, message)
        self.session.commit()

    def _ensure_stage_ready(self, analysis: Analysis, expected_stage: WorkflowStage) -> None:
        if analysis.current_stage != expected_stage:
            raise AppException(
                409,
                "workflow_stage_mismatch",
                f"Analysis is currently at '{analysis.current_stage}', not '{expected_stage}'.",
            )
        if analysis.status == AnalysisStatus.processing.value:
            step_state = ensure_workflow_state(analysis.workflow_state_json)[expected_stage]
            if str(step_state["status"]) == "processing":
                return
            raise AppException(409, "analysis_not_ready", "The requested stage is already processing.")
        if analysis.status not in {
            AnalysisStatus.awaiting_review.value,
            AnalysisStatus.completed.value,
        }:
            raise AppException(409, "analysis_not_ready", "The requested stage is not ready for user actions.")

    def _validate_reopen_target(self, *, analysis: Analysis, stage: WorkflowStage, entity_id: str | None) -> None:
        if stage == "icp_profiles" and entity_id is not None and not any(item.id == entity_id for item in analysis.icp_profiles):
            raise AppException(404, "icp_not_found", "ICP profile not found for this analysis.")
        if stage == "scenarios" and entity_id is not None and not any(item.id == entity_id for item in analysis.scenarios):
            raise AppException(404, "scenario_not_found", "Scenario not found for this analysis.")

    def _normalize_icp_segment_weights(self, analysis: Analysis) -> None:
        ordered_icps = sorted(analysis.icp_profiles, key=lambda item: (item.display_order, item.created_at))
        total = sum(max(0.0, icp.segment_weight) for icp in ordered_icps)
        if total <= 0:
            raise AppException(422, "invalid_icp_payload", "ICP segment weights must sum to a positive number.")

        normalized_values: list[float] = []
        for icp in ordered_icps:
            normalized_values.append(round(max(0.0, icp.segment_weight) / total, 4))
        drift = round(1.0 - sum(normalized_values), 4)
        if normalized_values:
            normalized_values[0] = round(normalized_values[0] + drift, 4)
        for icp, value in zip(ordered_icps, normalized_values, strict=True):
            icp.segment_weight = value

    def _sync_icp_entity(self, entity: ICPProfile, generated: GeneratedICP) -> None:
        entity.name = generated.name
        entity.description = generated.description
        entity.use_case = generated.use_case
        entity.goals_json = generated.goals
        entity.pain_points_json = generated.pain_points
        entity.decision_drivers_json = generated.decision_drivers
        entity.driver_weights_json = generated.driver_weights
        entity.price_sensitivity = generated.price_sensitivity
        entity.switching_cost = generated.switching_cost
        entity.alternatives_json = generated.alternatives
        entity.churn_threshold = generated.churn_threshold
        entity.retention_threshold = generated.retention_threshold
        entity.adoption_friction = generated.adoption_friction
        entity.value_perception_explanation = generated.value_perception_explanation
        entity.segment_weight = generated.segment_weight

    def _sync_scenario_entity(self, entity: Scenario, generated: GeneratedScenario) -> None:
        entity.title = generated.title
        entity.scenario_type = generated.scenario_type
        entity.description = generated.description
        entity.input_parameters_json = generated.input_parameters

    def _clear_downstream_from_product(self, analysis: Analysis) -> None:
        self._clear_feedback_events(analysis)
        self._clear_simulation_runs(analysis)
        self._clear_scenarios(analysis)
        self._clear_icps(analysis)

    def _clear_downstream_from_icps(self, analysis: Analysis) -> None:
        self._clear_feedback_events(analysis)
        self._clear_simulation_runs(analysis)
        self._clear_scenarios(analysis)

    def _clear_downstream_from_scenarios(self, analysis: Analysis) -> None:
        self._clear_feedback_events(analysis)
        self._clear_simulation_runs(analysis)

    def _clear_icps(self, analysis: Analysis) -> None:
        analysis.icp_profiles = []
        self.session.flush()

    def _clear_scenarios(self, analysis: Analysis) -> None:
        analysis.scenarios = []
        self.session.flush()

    def _clear_simulation_runs(self, analysis: Analysis) -> None:
        analysis.simulation_runs = []
        self.session.flush()

    def _clear_feedback_events(self, analysis: Analysis) -> None:
        self.session.execute(delete(FeedbackEvent).where(FeedbackEvent.analysis_id == analysis.id))

    def _icp_from_entity(self, entity: ICPProfile) -> GeneratedICP:
        return GeneratedICP(
            name=entity.name,
            description=entity.description,
            use_case=entity.use_case,
            goals=list(entity.goals_json),
            pain_points=list(entity.pain_points_json),
            decision_drivers=list(entity.decision_drivers_json),
            driver_weights=dict(entity.driver_weights_json),
            price_sensitivity=entity.price_sensitivity,
            switching_cost=entity.switching_cost,
            alternatives=list(entity.alternatives_json),
            churn_threshold=entity.churn_threshold,
            retention_threshold=entity.retention_threshold,
            adoption_friction=entity.adoption_friction,
            value_perception_explanation=entity.value_perception_explanation,
            segment_weight=entity.segment_weight,
        )
