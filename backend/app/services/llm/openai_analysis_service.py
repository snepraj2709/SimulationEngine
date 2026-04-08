from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, InternalServerError, RateLimitError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.models.scenario import ScenarioType
from app.schemas.product import ProductUnderstandingUpdateRequest
from app.schemas.simulation import ICPProfileUpdateRequest, ScenarioUpdateRequest
from app.services.domain_types import GeneratedICP, GeneratedScenario, ProductUnderstanding, ScrapeResult
from app.services.product_understanding_service import ProductUnderstandingService
from app.utils.text import dedupe_preserve_order, normalize_text, truncate_text

logger = get_logger(__name__)

DecisionDriver = Literal[
    "price_affordability",
    "value_for_money",
    "content_access",
    "mobile_experience",
    "brand_habit",
    "video_quality",
    "family_fit",
    "device_support",
    "regional_content",
    "feature_completeness",
    "automation_coverage",
    "analytics_depth",
    "implementation_complexity",
    "support_reliability",
    "team_enablement",
    "budget_predictability",
    "convenience",
]

ALLOWED_DECISION_DRIVERS: tuple[str, ...] = (
    "price_affordability",
    "value_for_money",
    "content_access",
    "mobile_experience",
    "brand_habit",
    "video_quality",
    "family_fit",
    "device_support",
    "regional_content",
    "feature_completeness",
    "automation_coverage",
    "analytics_depth",
    "implementation_complexity",
    "support_reliability",
    "team_enablement",
    "budget_predictability",
    "convenience",
)

_DEFAULT_CONFIDENCE_KEYS: tuple[str, ...] = (
    "company_name",
    "summary_line",
    "category",
    "buyer_type",
    "customer_logic",
    "pricing_model",
    "monetization_model",
    "feature_clusters",
    "business_model_signals",
    "simulation_levers",
)


class ProductCustomerLogicResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    core_job_to_be_done: str
    why_they_buy: list[str] = Field(min_length=2, max_length=5)
    why_they_hesitate: list[str] = Field(min_length=1, max_length=5)
    what_it_replaces: list[str] = Field(min_length=1, max_length=4)


class ProductFeatureClusterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    importance: Literal["high", "medium", "low"]
    description: str | None = None


class ProductUnderstandingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str
    product_name: str
    summary_line: str
    category: str
    subcategory: str
    buyer_type: str
    sales_motion: str
    pricing_model: str
    monetization_hypothesis: str
    customer_logic: ProductCustomerLogicResponse
    feature_clusters: list[ProductFeatureClusterResponse] = Field(min_length=2, max_length=6)
    confidence_score: float = Field(ge=0, le=1)
    confidence_scores: "ConfidenceScoresResponse"


class ConfidenceScoresResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: float = Field(ge=0, le=1)
    summary_line: float = Field(ge=0, le=1)
    category: float = Field(ge=0, le=1)
    buyer_type: float = Field(ge=0, le=1)
    customer_logic: float = Field(ge=0, le=1)
    pricing_model: float = Field(ge=0, le=1)
    monetization_model: float = Field(ge=0, le=1)
    feature_clusters: float = Field(ge=0, le=1)
    business_model_signals: float = Field(ge=0, le=1)
    simulation_levers: float = Field(ge=0, le=1)


class DriverWeightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    driver: DecisionDriver
    weight: float = Field(ge=0)


class GeneratedICPResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    use_case: str
    goals: list[str] = Field(min_length=2, max_length=6)
    pain_points: list[str] = Field(min_length=2, max_length=6)
    decision_drivers: list[DecisionDriver] = Field(min_length=3, max_length=6)
    driver_weights: list[DriverWeightResponse] = Field(min_length=3, max_length=6)
    price_sensitivity: float
    switching_cost: float
    alternatives: list[str] = Field(min_length=1, max_length=6)
    churn_threshold: float
    retention_threshold: float
    adoption_friction: float
    value_perception_explanation: str
    segment_weight: float


class GeneratedScenarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    scenario_type: ScenarioType
    description: str
    input_parameters: "ScenarioInputParametersResponse"


class ScenarioInputParametersResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_change_percent: float | None = None
    current_price_estimate: float | None = None
    removed_feature: str | None = None
    feature_importance: float | None = None
    premium_feature: str | None = None
    bundle_name: str | None = None
    bundle_price_change_percent: float | None = None
    service_name: str | None = None
    market: str | None = None
    plan_tier: str | None = None
    billing_period: str | None = None


class AnalysisArtifactsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    icps: list[GeneratedICPResponse] = Field(min_length=3, max_length=5)
    scenarios: list[GeneratedScenarioResponse] = Field(min_length=3, max_length=3)


class ICPArtifactsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    icps: list[GeneratedICPResponse] = Field(min_length=3, max_length=5)


class ScenarioArtifactsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenarios: list[GeneratedScenarioResponse] = Field(min_length=3, max_length=3)


class OpenAIAnalysisService:
    def __init__(self, client: AsyncOpenAI | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model

    async def generate_product_understanding(
        self,
        scrape_result: ScrapeResult,
        *,
        user_identifier: str,
    ) -> ProductUnderstanding:
        response = await self._call_with_retry(
            input_payload=self._stage_one_input(scrape_result),
            instructions=self._stage_one_instructions(),
            text_format=ProductUnderstandingResponse,
            max_output_tokens=1600,
            user_identifier=user_identifier,
        )
        payload = self._extract_parsed_output(response, stage="product understanding")
        return self._normalize_product_understanding(payload, scrape_result)

    async def generate_icps(
        self,
        understanding: ProductUnderstanding,
        *,
        user_identifier: str,
    ) -> list[GeneratedICP]:
        response = await self._call_with_retry(
            input_payload=self._stage_two_input(understanding),
            instructions=self._stage_two_instructions(),
            text_format=ICPArtifactsResponse,
            max_output_tokens=3600,
            user_identifier=user_identifier,
        )
        payload = self._extract_parsed_output(response, stage="ICP generation")
        return self._normalize_icp_artifacts(payload)

    async def generate_scenarios(
        self,
        understanding: ProductUnderstanding,
        icps: list[GeneratedICP],
        *,
        user_identifier: str,
    ) -> list[GeneratedScenario]:
        response = await self._call_with_retry(
            input_payload=self._stage_three_input(understanding, icps),
            instructions=self._stage_three_instructions(),
            text_format=ScenarioArtifactsResponse,
            max_output_tokens=3200,
            user_identifier=user_identifier,
        )
        payload = self._extract_parsed_output(response, stage="scenario generation")
        return self._normalize_scenario_artifacts(payload)

    async def generate_icps_and_scenarios(
        self,
        understanding: ProductUnderstanding,
        *,
        user_identifier: str,
    ) -> tuple[list[GeneratedICP], list[GeneratedScenario]]:
        icps = await self.generate_icps(understanding, user_identifier=user_identifier)
        scenarios = await self.generate_scenarios(understanding, icps, user_identifier=user_identifier)
        return icps, scenarios

    async def _call_with_retry(
        self,
        *,
        input_payload: list[dict[str, str]],
        instructions: str,
        text_format: type[BaseModel],
        max_output_tokens: int,
        user_identifier: str,
    ) -> Any:
        client = self._get_client()
        settings = get_settings()
        model = self._model or settings.openai_model
        last_error: Exception | None = None
        for attempt in range(2):
            request_max_output_tokens = max_output_tokens * (2 if attempt else 1)
            try:
                return await client.responses.parse(
                    model=model,
                    input=input_payload,
                    instructions=instructions,
                    text_format=text_format,
                    reasoning={"effort": "medium"},
                    max_output_tokens=request_max_output_tokens,
                    truncation="auto",
                    store=False,
                    user=user_identifier,
                )
            except (APITimeoutError, APIConnectionError, InternalServerError, RateLimitError) as exc:
                last_error = exc
                if attempt == 1:
                    break
                await asyncio.sleep(0.5)
            except ValidationError as exc:
                last_error = exc
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                raise AppException(422, "openai_invalid_output", "The analysis provider returned an invalid response.") from exc
            except APIStatusError as exc:
                last_error = exc
                if exc.status_code in {429, 500, 502, 503, 504} and attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                raise AppException(502, "openai_request_failed", "The analysis provider returned an error.") from exc

        raise AppException(502, "openai_request_failed", "The analysis provider could not complete the request.") from last_error

    def _get_client(self) -> AsyncOpenAI:
        if self._client is not None:
            return self._client
        settings = get_settings()
        if not settings.openai_api_key:
            raise AppException(503, "openai_not_configured", "OPENAI_API_KEY must be configured before analyzing a real URL.")
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    def _extract_parsed_output(self, response: Any, *, stage: str) -> BaseModel:
        parsed = getattr(response, "output_parsed", None)
        if parsed is not None:
            return parsed

        refusal = self._extract_refusal(response)
        if refusal:
            raise AppException(422, "openai_refusal", f"The analysis provider refused the {stage} request: {refusal}")

        raise AppException(422, "openai_invalid_output", f"The analysis provider returned an invalid {stage} response.")

    def _extract_refusal(self, response: Any) -> str | None:
        for output in getattr(response, "output", []):
            if getattr(output, "type", None) != "message":
                continue
            for item in getattr(output, "content", []):
                if getattr(item, "type", None) == "refusal":
                    refusal_text = getattr(item, "refusal", None)
                    if refusal_text:
                        return refusal_text
        return None

    def _stage_one_input(self, scrape_result: ScrapeResult) -> list[dict[str, str]]:
        scrape_payload = {
            "source_url": scrape_result.source_url,
            "final_url": scrape_result.final_url,
            "title": scrape_result.title,
            "meta_description": scrape_result.meta_description,
            "headings": scrape_result.headings[:10],
            "paragraphs": scrape_result.paragraphs[:12],
            "feature_clues": scrape_result.feature_clues[:10],
            "pricing_clues": scrape_result.pricing_clues[:10],
            "audience_clues": scrape_result.audience_clues[:10],
            "category_clues": scrape_result.category_clues[:10],
            "raw_text_excerpt": truncate_text(scrape_result.raw_text, 9000),
        }
        return [
            {"role": "user", "content": json.dumps(scrape_payload, ensure_ascii=True)},
        ]

    def _stage_one_instructions(self) -> str:
        return (
            "You analyze a scraped product or company webpage and return a structured business interpretation for downstream ICP generation and simulation. "
            "Use only the provided scrape payload. Do not assume facts from brand familiarity that are not supported by the input. "
            "Choose specific category and subcategory labels that match the page. "
            "Return a crisp one-line product summary, the most likely buyer type, customer buying logic, monetization clues, and concise feature clusters. "
            "Keep outputs compact and business-usable rather than descriptive or promotional. "
            "If evidence is thin, lower confidence instead of inventing certainty."
        )

    def _stage_two_input(self, understanding: ProductUnderstanding) -> list[dict[str, str]]:
        return [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "product_understanding": understanding.model_dump(
                            exclude={"normalized_json"},
                        ),
                        "allowed_decision_drivers": list(ALLOWED_DECISION_DRIVERS),
                        "allowed_scenario_types": [item.value for item in ScenarioType],
                    },
                    ensure_ascii=True,
                ),
            }
        ]

    def _stage_two_instructions(self) -> str:
        return (
            "Generate structured ICP profiles for the supplied product understanding. "
            "Use the buyer type, customer logic, monetization model, business signals, simulation levers, and uncertainties to make the ICPs specific. "
            "Return 3 to 5 ICPs. "
            "All ICP decision drivers must come only from the allowed decision driver vocabulary. "
            "Give each ICP a coherent weight distribution and segment weight, but do not worry about exact normalization because the application will normalize numeric fields."
        )

    def _stage_three_input(self, understanding: ProductUnderstanding, icps: list[GeneratedICP]) -> list[dict[str, str]]:
        return [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "product_understanding": understanding.model_dump(exclude={"normalized_json"}),
                        "icps": [icp.model_dump() for icp in icps],
                        "allowed_scenario_types": [item.value for item in ScenarioType],
                    },
                    ensure_ascii=True,
                ),
            }
        ]

    def _stage_three_instructions(self) -> str:
        return (
            "Generate exactly 3 structured scenario suggestions for the supplied product understanding and reviewed ICPs. "
            "Use the simulation levers, monetization model, switching friction, deployment complexity, and buying logic to keep the scenarios grounded. "
            "All scenario types must come only from the allowed scenario types. "
            "Make the scenarios realistic for the provided product and avoid any Netflix-specific assumptions unless the input explicitly supports them. "
            "Return the scenario title, type, concise description, and typed input parameters only."
        )

    def _normalize_product_understanding(
        self,
        payload: ProductUnderstandingResponse,
        scrape_result: ScrapeResult,
    ) -> ProductUnderstanding:
        feature_cluster_details = self._normalize_feature_clusters(payload.feature_clusters)
        confidence_scores = {
            key: self._clamp(getattr(payload.confidence_scores, key, payload.confidence_score), 0.0, 1.0)
            for key in _DEFAULT_CONFIDENCE_KEYS
        }

        understanding = ProductUnderstanding(
            company_name=truncate_text(payload.company_name.strip() or "Unknown Company", 120),
            product_name=truncate_text(payload.product_name.strip() or payload.company_name.strip() or "Unknown Product", 120),
            category=truncate_text(payload.category.strip() or "Unknown", 120),
            subcategory=truncate_text(payload.subcategory.strip() or "General Product Website", 120),
            positioning_summary=normalize_text(payload.summary_line.strip() or scrape_result.meta_description or scrape_result.title),
            pricing_model=normalize_text(payload.pricing_model.strip() or "usage_or_custom"),
            feature_clusters=[item["label"] for item in feature_cluster_details] or ["core product workflow", "customer value delivery"],
            monetization_hypothesis=truncate_text(payload.monetization_hypothesis.strip() or "Monetization requires further validation from the public page.", 220),
            target_customer_signals=[truncate_text(payload.buyer_type.strip(), 120)] if payload.buyer_type.strip() else ["general product evaluators"],
            confidence_score=self._clamp(payload.confidence_score, 0.0, 1.0),
            confidence_scores=confidence_scores,
            warnings=[],
            raw_extracted_json={
                **scrape_result.raw_extracted_json,
                "llm_analysis": {
                    "summary_line": payload.summary_line,
                    "buyer_type": payload.buyer_type,
                    "sales_motion": payload.sales_motion,
                    "customer_logic": payload.customer_logic.model_dump(),
                    "feature_clusters": feature_cluster_details,
                },
            },
            summary_line=truncate_text(payload.summary_line.strip() or scrape_result.meta_description or scrape_result.title, 180),
            buyer_type=truncate_text(payload.buyer_type.strip() or "General product evaluators", 120),
            sales_motion=truncate_text(payload.sales_motion.strip() or "", 120),
            customer_logic=payload.customer_logic.model_dump(),
            monetization_model={
                "pricing_visibility": "",
                "pricing_model": normalize_text(payload.pricing_model.strip() or "usage_or_custom"),
                "monetization_hypothesis": truncate_text(
                    payload.monetization_hypothesis.strip() or "Monetization requires further validation from the public page.",
                    220,
                ),
                "sales_motion": truncate_text(payload.sales_motion.strip() or "", 120),
            },
            feature_cluster_details=feature_cluster_details,
        )
        return ProductUnderstandingService().finalize(understanding, scrape_result=scrape_result)

    def _normalize_analysis_artifacts(
        self,
        payload: AnalysisArtifactsResponse,
    ) -> tuple[list[GeneratedICP], list[GeneratedScenario]]:
        return self._normalize_icp_artifacts(payload), self._normalize_scenario_artifacts(payload)

    def _normalize_icp_artifacts(
        self,
        payload: AnalysisArtifactsResponse | ICPArtifactsResponse,
    ) -> list[GeneratedICP]:
        icps = [self._normalize_icp(item) for item in payload.icps]
        if len(icps) < 3:
            raise AppException(422, "openai_invalid_output", "The analysis provider returned too few ICPs.")
        self._normalize_segment_weights(icps)
        return icps

    def _normalize_scenario_artifacts(
        self,
        payload: AnalysisArtifactsResponse | ScenarioArtifactsResponse,
    ) -> list[GeneratedScenario]:
        scenarios = [self._normalize_scenario(item) for item in payload.scenarios]
        if len(scenarios) != 3:
            raise AppException(422, "openai_invalid_output", "The analysis provider must return exactly 3 scenarios.")
        return scenarios

    def normalize_product_understanding_update(
        self,
        payload: ProductUnderstandingUpdateRequest,
        *,
        existing: ProductUnderstanding,
    ) -> ProductUnderstanding:
        feature_cluster_details = self._normalize_feature_clusters(payload.feature_clusters)
        understanding = ProductUnderstanding(
            company_name=truncate_text(payload.company_name.strip() or existing.company_name, 120),
            product_name=truncate_text(payload.product_name.strip() or existing.product_name, 120),
            category=truncate_text(payload.category.strip() or existing.category, 120),
            subcategory=truncate_text(payload.subcategory.strip() or existing.subcategory, 120),
            positioning_summary=normalize_text(payload.summary_line.strip() or existing.positioning_summary),
            pricing_model=normalize_text(payload.monetization_model.pricing_model.strip() or existing.pricing_model),
            feature_clusters=[item["label"] for item in feature_cluster_details] or existing.feature_clusters,
            monetization_hypothesis=truncate_text(
                payload.monetization_model.monetization_hypothesis.strip() or existing.monetization_hypothesis,
                220,
            ),
            target_customer_signals=[truncate_text(payload.buyer_type.strip(), 120)] if payload.buyer_type.strip() else existing.target_customer_signals,
            confidence_score=existing.confidence_score,
            confidence_scores=dict(existing.confidence_scores),
            warnings=[item.reason for item in payload.uncertainties[:6]],
            raw_extracted_json=dict(existing.raw_extracted_json),
            summary_line=truncate_text(payload.summary_line.strip() or existing.summary_line or existing.positioning_summary, 180),
            buyer_type=truncate_text(payload.buyer_type.strip() or existing.buyer_type, 120),
            sales_motion=truncate_text(
                payload.monetization_model.sales_motion.strip() or existing.sales_motion or existing.monetization_model.sales_motion,
                120,
            ),
            business_model_signals=[item.model_dump() for item in payload.business_model_signals],
            customer_logic=payload.customer_logic.model_dump(),
            monetization_model=payload.monetization_model.model_dump(),
            feature_cluster_details=feature_cluster_details,
            simulation_levers=[item.model_dump() for item in payload.simulation_levers],
            uncertainties=[item.model_dump() for item in payload.uncertainties],
            source_coverage=existing.source_coverage.model_dump(),
        )
        return ProductUnderstandingService().finalize(understanding)

    def normalize_icp_update(self, payload: ICPProfileUpdateRequest) -> GeneratedICP:
        decision_drivers = self._normalize_string_list(payload.decision_drivers, limit=6)
        decision_drivers = [driver for driver in decision_drivers if driver in ALLOWED_DECISION_DRIVERS]
        if len(decision_drivers) < 3:
            raise AppException(422, "invalid_icp_payload", "Each ICP must include at least 3 valid decision drivers.")

        driver_weights: dict[str, float] = {}
        for item in payload.driver_weights:
            if item.driver in decision_drivers and item.driver not in driver_weights:
                driver_weights[item.driver] = max(0.0, float(item.weight))
        for driver in decision_drivers:
            driver_weights.setdefault(driver, 0.0)
        driver_weights = self._normalize_weights(driver_weights)

        return GeneratedICP(
            name=truncate_text(payload.name.strip(), 120),
            description=truncate_text(payload.description.strip(), 220),
            use_case=truncate_text(payload.use_case.strip(), 180),
            goals=self._normalize_string_list(payload.goals, limit=6),
            pain_points=self._normalize_string_list(payload.pain_points, limit=6),
            decision_drivers=decision_drivers,
            driver_weights=driver_weights,
            price_sensitivity=self._clamp(payload.price_sensitivity, 0.0, 1.0),
            switching_cost=self._clamp(payload.switching_cost, 0.0, 1.0),
            alternatives=self._normalize_string_list(payload.alternatives, limit=6),
            churn_threshold=self._clamp(payload.churn_threshold, -0.35, -0.05),
            retention_threshold=self._clamp(payload.retention_threshold, 0.02, 0.15),
            adoption_friction=self._clamp(payload.adoption_friction, 0.0, 1.0),
            value_perception_explanation=truncate_text(payload.value_perception_explanation.strip(), 220),
            segment_weight=max(0.01, float(payload.segment_weight)),
        )

    def normalize_scenario_update(self, payload: ScenarioUpdateRequest) -> GeneratedScenario:
        parameters = {key: value for key, value in payload.input_parameters.items() if value is not None}
        scenario_type = payload.scenario_type

        if scenario_type not in {item.value for item in ScenarioType}:
            raise AppException(422, "invalid_scenario_payload", "Scenario type is not supported.")

        if scenario_type == ScenarioType.pricing_increase.value:
            parameters["price_change_percent"] = abs(
                self._required_float(parameters, "price_change_percent", minimum=0.1, maximum=50.0)
            )
        elif scenario_type == ScenarioType.pricing_decrease.value:
            parameters["price_change_percent"] = -abs(
                self._required_float(parameters, "price_change_percent", minimum=0.1, maximum=50.0)
            )
        elif scenario_type == ScenarioType.feature_removal.value:
            parameters["removed_feature"] = self._required_string(parameters, "removed_feature")
            parameters["feature_importance"] = self._required_float(
                parameters,
                "feature_importance",
                minimum=0.05,
                maximum=1.0,
            )
        elif scenario_type == ScenarioType.premium_feature_addition.value:
            parameters["premium_feature"] = self._required_string(parameters, "premium_feature")
            if "price_change_percent" in parameters:
                parameters["price_change_percent"] = abs(
                    self._optional_float(parameters, "price_change_percent", minimum=0.0, maximum=50.0)
                )
        elif scenario_type == ScenarioType.bundling.value:
            parameters["bundle_name"] = self._required_string(parameters, "bundle_name")
            if "bundle_price_change_percent" in parameters:
                parameters["bundle_price_change_percent"] = abs(
                    self._optional_float(parameters, "bundle_price_change_percent", minimum=0.0, maximum=50.0)
                )
        elif scenario_type == ScenarioType.unbundling.value:
            parameters["service_name"] = self._required_string(parameters, "service_name")
            if "price_change_percent" in parameters:
                parameters["price_change_percent"] = -abs(
                    self._optional_float(parameters, "price_change_percent", minimum=0.0, maximum=50.0)
                )

        if "current_price_estimate" in parameters:
            parameters["current_price_estimate"] = max(1.0, float(parameters["current_price_estimate"]))

        if "market" in parameters:
            parameters["market"] = truncate_text(str(parameters["market"]).strip(), 64)
        if "plan_tier" in parameters:
            parameters["plan_tier"] = truncate_text(str(parameters["plan_tier"]).strip(), 64)
        if "billing_period" in parameters:
            parameters["billing_period"] = truncate_text(str(parameters["billing_period"]).strip(), 64)

        return GeneratedScenario(
            title=truncate_text(payload.title.strip(), 140),
            scenario_type=scenario_type,
            description=truncate_text(payload.description.strip(), 240),
            input_parameters=parameters,
        )

    def _normalize_icp(self, payload: GeneratedICPResponse) -> GeneratedICP:
        decision_drivers = self._normalize_string_list(payload.decision_drivers, limit=6)
        decision_drivers = [driver for driver in decision_drivers if driver in ALLOWED_DECISION_DRIVERS]
        if len(decision_drivers) < 3:
            raise AppException(422, "openai_invalid_output", "Each ICP must include at least 3 valid decision drivers.")

        driver_weights = {}
        for item in payload.driver_weights:
            if item.driver in decision_drivers and item.driver not in driver_weights:
                driver_weights[item.driver] = max(0.0, float(item.weight))
        for driver in decision_drivers:
            driver_weights.setdefault(driver, 0.0)
        driver_weights = self._normalize_weights(driver_weights)

        return GeneratedICP(
            name=truncate_text(payload.name.strip(), 120),
            description=truncate_text(payload.description.strip(), 220),
            use_case=truncate_text(payload.use_case.strip(), 180),
            goals=self._normalize_string_list(payload.goals, limit=6),
            pain_points=self._normalize_string_list(payload.pain_points, limit=6),
            decision_drivers=decision_drivers,
            driver_weights=driver_weights,
            price_sensitivity=self._clamp(payload.price_sensitivity, 0.0, 1.0),
            switching_cost=self._clamp(payload.switching_cost, 0.0, 1.0),
            alternatives=self._normalize_string_list(payload.alternatives, limit=6),
            churn_threshold=self._clamp(payload.churn_threshold, -0.35, -0.05),
            retention_threshold=self._clamp(payload.retention_threshold, 0.02, 0.15),
            adoption_friction=self._clamp(payload.adoption_friction, 0.0, 1.0),
            value_perception_explanation=truncate_text(payload.value_perception_explanation.strip(), 220),
            segment_weight=max(0.01, float(payload.segment_weight)),
        )

    def _normalize_scenario(self, payload: GeneratedScenarioResponse) -> GeneratedScenario:
        parameters = {key: value for key, value in payload.input_parameters.model_dump().items() if value is not None}
        scenario_type = payload.scenario_type.value

        if scenario_type == ScenarioType.pricing_increase.value:
            parameters["price_change_percent"] = abs(self._required_float(parameters, "price_change_percent", minimum=0.1, maximum=50.0))
        elif scenario_type == ScenarioType.pricing_decrease.value:
            parameters["price_change_percent"] = -abs(self._required_float(parameters, "price_change_percent", minimum=0.1, maximum=50.0))
        elif scenario_type == ScenarioType.feature_removal.value:
            parameters["removed_feature"] = self._required_string(parameters, "removed_feature")
            parameters["feature_importance"] = self._required_float(parameters, "feature_importance", minimum=0.05, maximum=1.0)
        elif scenario_type == ScenarioType.premium_feature_addition.value:
            parameters["premium_feature"] = self._required_string(parameters, "premium_feature")
            if "price_change_percent" in parameters:
                parameters["price_change_percent"] = abs(self._optional_float(parameters, "price_change_percent", minimum=0.0, maximum=50.0))
        elif scenario_type == ScenarioType.bundling.value:
            parameters["bundle_name"] = self._required_string(parameters, "bundle_name")
            if "bundle_price_change_percent" in parameters:
                parameters["bundle_price_change_percent"] = abs(self._optional_float(parameters, "bundle_price_change_percent", minimum=0.0, maximum=50.0))
        elif scenario_type == ScenarioType.unbundling.value:
            parameters["service_name"] = self._required_string(parameters, "service_name")
            if "price_change_percent" in parameters:
                parameters["price_change_percent"] = -abs(self._optional_float(parameters, "price_change_percent", minimum=0.0, maximum=50.0))

        if "current_price_estimate" in parameters:
            parameters["current_price_estimate"] = max(1.0, float(parameters["current_price_estimate"]))

        if "market" in parameters:
            parameters["market"] = truncate_text(str(parameters["market"]).strip(), 64)
        if "plan_tier" in parameters:
            parameters["plan_tier"] = truncate_text(str(parameters["plan_tier"]).strip(), 64)
        if "billing_period" in parameters:
            parameters["billing_period"] = truncate_text(str(parameters["billing_period"]).strip(), 64)

        return GeneratedScenario(
            title=truncate_text(payload.title.strip(), 140),
            scenario_type=scenario_type,
            description=truncate_text(payload.description.strip(), 240),
            input_parameters=parameters,
        )

    def _normalize_segment_weights(self, icps: list[GeneratedICP]) -> None:
        total = sum(max(0.0, icp.segment_weight) for icp in icps)
        if total <= 0:
            raise AppException(422, "openai_invalid_output", "ICP segment weights must sum to a positive number.")
        for icp in icps:
            icp.segment_weight = round(max(0.0, icp.segment_weight) / total, 4)

        drift = round(1.0 - sum(icp.segment_weight for icp in icps), 4)
        if icps and drift != 0:
            icps[0].segment_weight = round(icps[0].segment_weight + drift, 4)

    def _normalize_weights(self, weights: dict[str, float]) -> dict[str, float]:
        total = sum(weights.values())
        if total <= 0:
            equal_weight = round(1.0 / len(weights), 4)
            normalized = {driver: equal_weight for driver in weights}
            drift = round(1.0 - sum(normalized.values()), 4)
            first_driver = next(iter(normalized))
            normalized[first_driver] = round(normalized[first_driver] + drift, 4)
            return normalized

        normalized = {
            driver: round(weight / total, 4)
            for driver, weight in weights.items()
        }
        drift = round(1.0 - sum(normalized.values()), 4)
        first_driver = next(iter(normalized))
        normalized[first_driver] = round(normalized[first_driver] + drift, 4)
        return normalized

    def _normalize_string_list(self, values: list[str], *, limit: int) -> list[str]:
        cleaned = [truncate_text(str(value).strip(), 160) for value in values if str(value).strip()]
        return dedupe_preserve_order(cleaned)[:limit]

    def _normalize_feature_clusters(self, values: list[ProductFeatureClusterResponse], *, limit: int = 6) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in values:
            label = truncate_text(item.label.strip(), 60)
            if not label:
                continue
            lowered = label.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(
                {
                    "key": normalize_text(label).lower().replace(" ", "-"),
                    "label": label,
                    "importance": item.importance,
                    "description": truncate_text(item.description.strip(), 140) if item.description and item.description.strip() else None,
                }
            )
        return normalized[:limit]

    def _required_float(self, values: dict[str, Any], key: str, *, minimum: float, maximum: float) -> float:
        if key not in values:
            raise AppException(422, "openai_invalid_output", f"Scenario input is missing required field '{key}'.")
        return self._clamp(float(values[key]), minimum, maximum)

    def _optional_float(self, values: dict[str, Any], key: str, *, minimum: float, maximum: float) -> float:
        return self._clamp(float(values[key]), minimum, maximum)

    def _required_string(self, values: dict[str, Any], key: str) -> str:
        value = str(values.get(key, "")).strip()
        if not value:
            raise AppException(422, "openai_invalid_output", f"Scenario input is missing required field '{key}'.")
        return truncate_text(value, 120)

    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        return round(min(maximum, max(minimum, float(value))), 4)
