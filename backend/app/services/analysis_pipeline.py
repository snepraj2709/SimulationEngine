from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.analysis import Analysis
from app.models.extracted_product_data import ExtractedProductData
from app.models.icp_profile import ICPProfile
from app.models.scenario import Scenario
from app.models.simulation import SimulationResult, SimulationRun
from app.repositories.analysis_repository import AnalysisRepository
from app.services.domain_types import GeneratedICP, GeneratedScenario
from app.services.icp_generation_service import ICPGenerationService
from app.services.outcome_aggregator import OutcomeAggregator
from app.services.product_understanding_service import ProductUnderstandingService
from app.services.scenario_generation_service import ScenarioGenerationService
from app.services.scraper_service import ScraperService
from app.services.simulation_engine import SimulationEngine

logger = get_logger(__name__)


class AnalysisPipelineService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AnalysisRepository(session)
        self.scraper = ScraperService()
        self.product_understanding = ProductUnderstandingService()
        self.icp_generation = ICPGenerationService()
        self.scenario_generation = ScenarioGenerationService()
        self.simulation_engine = SimulationEngine()
        self.outcome_aggregator = OutcomeAggregator()

    async def process_analysis(self, analysis_id: str) -> None:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis is None:
            raise AppException(404, "analysis_not_found", "Analysis not found.")

        self.repository.mark_processing(analysis)
        self.session.commit()
        try:
            scrape_result = await self.scraper.scrape(analysis.normalized_url)
            understanding = self.product_understanding.build(scrape_result)
            analysis.extracted_product_data = ExtractedProductData(
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
            )

            generated_icps = self.icp_generation.generate(understanding)
            icp_entities = [self._persist_icp(analysis, icp) for icp in generated_icps]
            generated_scenarios = self.scenario_generation.generate(understanding, generated_icps)
            scenario_entities = [self._persist_scenario(analysis, scenario) for scenario in generated_scenarios]
            self.session.flush()

            for scenario_entity, generated_scenario in zip(scenario_entities, generated_scenarios, strict=True):
                self._create_simulation_run(analysis, scenario_entity, understanding, generated_icps, icp_entities, generated_scenario)

            self.repository.mark_completed(analysis)
            self.session.commit()
            logger.info(
                "Analysis completed",
                extra={
                    "extra_data": {
                        "analysis_id": analysis.id,
                        "normalized_url": analysis.normalized_url,
                    }
                },
            )
        except AppException as exc:
            self.session.rollback()
            self._mark_failed(analysis_id, exc.detail)
        except Exception as exc:  # pragma: no cover - safety net
            self.session.rollback()
            logger.exception("Unexpected analysis failure", extra={"extra_data": {"analysis_id": analysis_id}})
            self._mark_failed(analysis_id, "Analysis pipeline failed unexpectedly.")
            raise exc

    async def rerun_scenario(self, *, analysis: Analysis, scenario: Scenario, input_overrides: dict, run_version: str) -> SimulationRun:
        if analysis.status != "completed":
            raise AppException(409, "analysis_not_ready", "Simulation cannot run until analysis is complete.")
        product = analysis.extracted_product_data
        if product is None:
            raise AppException(409, "analysis_incomplete", "Simulation cannot run without product understanding.")
        understanding = self.product_understanding.build_from_normalized(product.normalized_json)
        generated_icps = [self._icp_from_entity(icp) for icp in analysis.icp_profiles]
        generated_scenario = GeneratedScenario(
            title=scenario.title,
            scenario_type=str(scenario.scenario_type),
            description=scenario.description,
            input_parameters={**scenario.input_parameters_json, **input_overrides},
        )
        run = self._create_simulation_run(analysis, scenario, understanding, generated_icps, analysis.icp_profiles, generated_scenario, run_version=run_version)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def _persist_icp(self, analysis: Analysis, generated: GeneratedICP) -> ICPProfile:
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
        )
        analysis.icp_profiles.append(entity)
        return entity

    def _persist_scenario(self, analysis: Analysis, generated: GeneratedScenario) -> Scenario:
        entity = Scenario(
            title=generated.title,
            scenario_type=generated.scenario_type,
            description=generated.description,
            input_parameters_json=generated.input_parameters,
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

    def _mark_failed(self, analysis_id: str, message: str) -> None:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis is None:
            return
        self.repository.mark_failed(analysis, message)
        self.session.commit()

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
