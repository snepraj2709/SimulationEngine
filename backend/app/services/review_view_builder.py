from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.analysis import Analysis
from app.models.icp_profile import ICPProfile
from app.models.scenario import Scenario, ScenarioType
from app.schemas.simulation import (
    BehavioralSignalResponse,
    ConfidenceIndicatorResponse,
    DecisionDriverViewResponse,
    EditableFieldConfigResponse,
    ICPBuyingLogicResponse,
    ICPViewModelResponse,
    ScenarioExecutionEffortResponse,
    ScenarioExpectedImpactResponse,
    ScenarioLinkedICPSummaryResponse,
    ScenarioMetadataResponse,
    ScenarioRecommendationResponse,
    ScenarioReviewViewResponse,
    SimulationImpactItemResponse,
)
from app.services.domain_types import AggregatedScenarioOutcome, GeneratedICP, GeneratedScenario, ProductUnderstanding, SimulationComputationResult
from app.services.outcome_aggregator import OutcomeAggregator
from app.services.product_understanding_service import ProductUnderstandingService
from app.services.simulation_engine import SimulationEngine
from app.utils.text import dedupe_preserve_order, normalize_text, truncate_text

CHURN_THRESHOLD_MIN = -0.35
CHURN_THRESHOLD_MAX = -0.05
RETENTION_THRESHOLD_MIN = 0.02
RETENTION_THRESHOLD_MAX = 0.15
SIGNAL_SCALE_MIN = 1
SIGNAL_SCALE_MAX = 5

SIGNAL_LABELS: dict[str, str] = {
    "priceSensitivity": "Price Sensitivity",
    "switchingFriction": "Switching Friction",
    "timeToValueExpectation": "Time-to-Value Expectation",
    "proofRequirement": "Proof Requirement",
    "implementationTolerance": "Implementation Tolerance",
    "retentionStability": "Retention Stability",
}

SIGNAL_ORDER: tuple[str, ...] = (
    "priceSensitivity",
    "switchingFriction",
    "timeToValueExpectation",
    "proofRequirement",
    "implementationTolerance",
    "retentionStability",
)


@dataclass
class ScenarioReviewComputation:
    scenario: Scenario
    review_view: ScenarioReviewViewResponse
    ranking_score: float


def build_icp_view_model(profile: ICPProfile, *, understanding: ProductUnderstanding | None = None) -> ICPViewModelResponse:
    generated_icp = _generated_icp_from_profile(profile)
    signals = _build_behavioral_signals(generated_icp)
    decision_drivers = _build_decision_driver_rows(generated_icp)
    return ICPViewModelResponse(
        id=profile.id or f"icp-{profile.display_order}",
        segment_name=profile.name,
        segment_summary=_build_segment_summary(profile.description, profile.use_case),
        estimated_segment_share=round(profile.segment_weight * 100, 1),
        confidence=_build_icp_confidence(profile, understanding),
        best_fit_use_case=profile.use_case,
        buying_logic=_build_buying_logic(generated_icp),
        behavioral_signals=signals,
        decision_drivers=decision_drivers,
        simulation_impact=_build_icp_simulation_impact(signals, decision_drivers),
        editable_fields=_build_icp_editable_fields(),
    )


def build_scenario_review_views(analysis: Analysis) -> dict[str, ScenarioReviewViewResponse]:
    understanding = _build_understanding(analysis)
    if understanding is None or not analysis.icp_profiles or not analysis.scenarios:
        return {}

    ordered_profiles = sorted(analysis.icp_profiles, key=_ordered_entity_key)
    ordered_scenarios = sorted(analysis.scenarios, key=_ordered_entity_key)
    generated_icps = [_generated_icp_from_profile(profile) for profile in ordered_profiles]
    signal_lookup = {
        _entity_identifier(profile, prefix="icp"): {signal.signal_key: signal for signal in _build_behavioral_signals(generated_icp)}
        for profile, generated_icp in zip(ordered_profiles, generated_icps, strict=True)
    }

    engine = SimulationEngine()
    aggregator = OutcomeAggregator()
    computations: list[ScenarioReviewComputation] = []

    for scenario in ordered_scenarios:
        generated_scenario = _generated_scenario_from_entity(scenario)
        results = [
            engine.simulate(understanding=understanding, icp=generated_icp, scenario=generated_scenario)
            for generated_icp in generated_icps
        ]
        aggregate = aggregator.aggregate(
            scenario_id=_entity_identifier(scenario, prefix="scenario"),
            scenario_title=scenario.title,
            icps=generated_icps,
            results=results,
        )
        dominant_icp = _select_primary_icp(ordered_profiles, results)
        relevant_signals = _select_relevant_signals(
            signal_lookup.get(_entity_identifier(dominant_icp, prefix="icp"), {}),
            scenario_type=str(scenario.scenario_type),
        )
        expected_impact = _build_expected_impacts(
            scenario=scenario,
            aggregate=aggregate,
            signals=signal_lookup,
            profiles=ordered_profiles,
            understanding=understanding,
        )
        execution_effort = _build_execution_effort(scenario)
        review_view = ScenarioReviewViewResponse(
            id=_entity_identifier(scenario, prefix="scenario"),
            scenario_type=str(scenario.scenario_type),
            scenario_title=scenario.title,
            scenario_summary=truncate_text(normalize_text(scenario.description), 160),
            short_decision_statement=_build_short_decision_statement(scenario),
            recommendation=ScenarioRecommendationResponse(
                priority_rank=1,
                recommendation_label="Worth testing",
                recommendation_reason="Modeled upside and execution effort look balanced.",
            ),
            expected_impact=expected_impact,
            why_this_might_work=_build_why_this_might_work(
                scenario=scenario,
                dominant_icp=dominant_icp,
                relevant_signals=relevant_signals,
                aggregate=aggregate,
            ),
            tradeoffs=_build_tradeoffs(scenario),
            execution_effort=execution_effort,
            linked_icp_summary=ScenarioLinkedICPSummaryResponse(
                segment_name=dominant_icp.name,
                relevant_signals=relevant_signals,
            ),
            raw_parameters=dict(scenario.input_parameters_json),
            metadata=_build_scenario_metadata(scenario),
        )
        computations.append(
            ScenarioReviewComputation(
                scenario=scenario,
                review_view=review_view,
                ranking_score=_score_scenario_review(review_view, execution_effort),
            )
        )

    ranked = sorted(computations, key=lambda item: item.ranking_score, reverse=True)
    total = len(ranked)
    for index, computation in enumerate(ranked, start=1):
        recommendation = _build_recommendation(
            review_view=computation.review_view,
            ranking_score=computation.ranking_score,
            priority_rank=index,
            total=total,
        )
        computation.review_view.recommendation = recommendation
    return {_entity_identifier(computation.scenario, prefix="scenario"): computation.review_view for computation in computations}


def _build_understanding(analysis: Analysis) -> ProductUnderstanding | None:
    product_data = getattr(analysis, "extracted_product_data", None)
    if not product_data:
        return None
    return ProductUnderstandingService().build_from_normalized(product_data.normalized_json)


def _generated_icp_from_profile(profile: ICPProfile) -> GeneratedICP:
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


def _generated_scenario_from_entity(scenario: Scenario) -> GeneratedScenario:
    return GeneratedScenario(
        title=scenario.title,
        scenario_type=str(scenario.scenario_type),
        description=scenario.description,
        input_parameters=dict(scenario.input_parameters_json),
    )


def _build_segment_summary(description: str, use_case: str) -> str:
    combined = normalize_text(f"{description} {use_case}")
    return truncate_text(combined, 118)


def _build_icp_confidence(
    profile: ICPProfile,
    understanding: ProductUnderstanding | None,
) -> ConfidenceIndicatorResponse | None:
    if understanding is None:
        return None
    completeness = (
        min(len(profile.goals_json), 3) / 3
        + min(len(profile.pain_points_json), 3) / 3
        + min(len(profile.decision_drivers_json), 4) / 4
    ) / 3
    score = max(0.0, min(1.0, round(understanding.confidence_score * 0.72 + completeness * 0.28, 2)))
    return ConfidenceIndicatorResponse(
        score=score,
        label=_confidence_label(score),
        source="derived",
    )


def _build_buying_logic(icp: GeneratedICP) -> ICPBuyingLogicResponse:
    wins_with = dedupe_preserve_order(
        [
            icp.use_case,
            *_split_sentences(icp.value_perception_explanation),
        ]
    )
    return ICPBuyingLogicResponse(
        buys_for=_compress_list(icp.goals, limit=2),
        avoids_because=_compress_list(icp.pain_points, limit=2),
        wins_with=_compress_list(wins_with, limit=2),
    )


def _build_behavioral_signals(icp: GeneratedICP) -> list[BehavioralSignalResponse]:
    time_to_value_raw = max(
        0.0,
        min(
            1.0,
            (1 - icp.adoption_friction) * 0.55
            + icp.price_sensitivity * 0.25
            + (1 - icp.switching_cost) * 0.20,
        ),
    )
    rows = [
        BehavioralSignalResponse(
            signal_key="priceSensitivity",
            label=SIGNAL_LABELS["priceSensitivity"],
            value_1_to_5=_normalize_signal(icp.price_sensitivity, 0.0, 1.0),
            editable=True,
            derived=False,
            source_field="price_sensitivity",
        ),
        BehavioralSignalResponse(
            signal_key="switchingFriction",
            label=SIGNAL_LABELS["switchingFriction"],
            value_1_to_5=_normalize_signal(icp.switching_cost, 0.0, 1.0),
            editable=True,
            derived=False,
            source_field="switching_cost",
        ),
        BehavioralSignalResponse(
            signal_key="timeToValueExpectation",
            label=SIGNAL_LABELS["timeToValueExpectation"],
            value_1_to_5=_normalize_signal(time_to_value_raw, 0.0, 1.0),
            editable=False,
            derived=True,
            source_field=None,
        ),
        BehavioralSignalResponse(
            signal_key="proofRequirement",
            label=SIGNAL_LABELS["proofRequirement"],
            value_1_to_5=_normalize_signal(icp.retention_threshold, RETENTION_THRESHOLD_MIN, RETENTION_THRESHOLD_MAX),
            editable=True,
            derived=False,
            source_field="retention_threshold",
        ),
        BehavioralSignalResponse(
            signal_key="implementationTolerance",
            label=SIGNAL_LABELS["implementationTolerance"],
            value_1_to_5=_normalize_signal(icp.adoption_friction, 1.0, 0.0),
            editable=True,
            derived=True,
            source_field="adoption_friction",
        ),
        BehavioralSignalResponse(
            signal_key="retentionStability",
            label=SIGNAL_LABELS["retentionStability"],
            value_1_to_5=_normalize_signal(icp.churn_threshold, CHURN_THRESHOLD_MAX, CHURN_THRESHOLD_MIN),
            editable=True,
            derived=True,
            source_field="churn_threshold",
        ),
    ]
    return rows


def _build_decision_driver_rows(icp: GeneratedICP) -> list[DecisionDriverViewResponse]:
    ranked = sorted(
        [(driver, float(icp.driver_weights.get(driver, 0.0))) for driver in _selected_drivers(icp)],
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        DecisionDriverViewResponse(
            key=driver,
            label=_format_driver_label(driver),
            weight_percent=max(0, min(100, round(weight * 100))),
            rank=index + 1,
        )
        for index, (driver, weight) in enumerate(ranked)
    ]


def _build_icp_simulation_impact(
    signals: list[BehavioralSignalResponse],
    decision_drivers: list[DecisionDriverViewResponse],
) -> list[SimulationImpactItemResponse]:
    signal_map = {signal.signal_key: signal for signal in signals}
    top_driver = decision_drivers[0].label if decision_drivers else "Perceived value"

    price = signal_map["priceSensitivity"].value_1_to_5
    switching = signal_map["switchingFriction"].value_1_to_5
    ttv = signal_map["timeToValueExpectation"].value_1_to_5
    implementation = signal_map["implementationTolerance"].value_1_to_5
    proof = signal_map["proofRequirement"].value_1_to_5
    retention = signal_map["retentionStability"].value_1_to_5

    impacts = [
        SimulationImpactItemResponse(
            title="Pricing will move evaluation quickly" if price >= 4 else "Pricing changes have moderate impact",
            explanation=(
                f"{SIGNAL_LABELS['priceSensitivity']} is {_level_word(price)}, so offer changes are likely to shift "
                f"conversion before {top_driver.lower()} concerns disappear."
            ),
            severity=_severity_from_level(price),
        ),
        SimulationImpactItemResponse(
            title="Activation depends on fast proof" if ttv >= 4 or implementation <= 2 else "Activation risk is manageable",
            explanation=(
                f"{SIGNAL_LABELS['timeToValueExpectation']} is {_level_word(ttv)} and "
                f"{SIGNAL_LABELS['implementationTolerance']} is {_level_word(implementation)}, so rollout speed will shape early adoption."
            ),
            severity=_severity_from_level(max(ttv, 6 - implementation)),
        ),
        SimulationImpactItemResponse(
            title="Retention is vulnerable to weak rollout" if retention <= 2 or proof >= 4 else "Retention should hold if value stays obvious",
            explanation=(
                f"{SIGNAL_LABELS['proofRequirement']} is {_level_word(proof)} and "
                f"{SIGNAL_LABELS['retentionStability']} is {_level_word(retention)}, so trust and proof quality will determine renewal behavior."
            ),
            severity=_severity_from_level(max(proof, 6 - retention)),
        ),
    ]
    if switching >= 4:
        impacts[0].explanation = (
            f"{SIGNAL_LABELS['priceSensitivity']} is {_level_word(price)} and {SIGNAL_LABELS['switchingFriction']} is high, "
            "so pricing changes matter, but the segment still needs a clear reason to move."
        )
    return impacts


def _build_icp_editable_fields() -> list[EditableFieldConfigResponse]:
    return [
        EditableFieldConfigResponse(field="segment_name", label="Segment name", control="text"),
        EditableFieldConfigResponse(field="segment_share", label="Segment share", control="percentage", min=1, max=100),
        EditableFieldConfigResponse(field="priceSensitivity", label=SIGNAL_LABELS["priceSensitivity"], control="dot_scale", min=1, max=5),
        EditableFieldConfigResponse(field="switchingFriction", label=SIGNAL_LABELS["switchingFriction"], control="dot_scale", min=1, max=5),
        EditableFieldConfigResponse(field="proofRequirement", label=SIGNAL_LABELS["proofRequirement"], control="dot_scale", min=1, max=5),
        EditableFieldConfigResponse(field="implementationTolerance", label=SIGNAL_LABELS["implementationTolerance"], control="dot_scale", min=1, max=5),
        EditableFieldConfigResponse(field="retentionStability", label=SIGNAL_LABELS["retentionStability"], control="dot_scale", min=1, max=5),
        EditableFieldConfigResponse(
            field="timeToValueExpectation",
            label=SIGNAL_LABELS["timeToValueExpectation"],
            control="dot_scale",
            editable=False,
            min=1,
            max=5,
        ),
        EditableFieldConfigResponse(field="decisionDrivers", label="Top decision drivers", control="ranked_driver_editor"),
    ]


def _select_primary_icp(profiles: list[ICPProfile], results: list[SimulationComputationResult]) -> ICPProfile:
    ranked = sorted(
        zip(profiles, results, strict=True),
        key=lambda item: abs(item[1].delta_score) * max(0.05, item[0].segment_weight),
        reverse=True,
    )
    return ranked[0][0]


def _build_expected_impacts(
    *,
    scenario: Scenario,
    aggregate: AggregatedScenarioOutcome,
    signals: dict[str, dict[str, BehavioralSignalResponse]],
    profiles: list[ICPProfile],
    understanding: ProductUnderstanding,
) -> list[ScenarioExpectedImpactResponse]:
    average_signals = _weighted_average_signals(signals, profiles)
    price_change = float(
        scenario.input_parameters_json.get("price_change_percent")
        or scenario.input_parameters_json.get("bundle_price_change_percent")
        or 0.0
    )
    revenue = _impact_range(
        label="Revenue",
        metric_key="revenue",
        center=aggregate.estimated_revenue_delta_pct,
        confidence=_confidence_label(understanding.confidence_score),
    )
    conversion = _impact_range(
        label="Conversion",
        metric_key="conversion",
        center=_derive_conversion_change_pct(str(scenario.scenario_type), price_change, average_signals),
        confidence=_confidence_label(understanding.confidence_score * 0.92),
    )
    activation = _impact_range(
        label="Activation speed",
        metric_key="activation_speed",
        center=_derive_activation_change_pct(str(scenario.scenario_type), average_signals),
        confidence=_confidence_label(understanding.confidence_score * 0.84),
    )
    churn = _impact_range(
        label="Churn risk",
        metric_key="churn_risk",
        center=_derive_churn_risk_change_pct(str(scenario.scenario_type), aggregate, average_signals),
        invert_business_direction=True,
        confidence=_confidence_label(understanding.confidence_score * 0.88),
    )
    return [revenue, conversion, churn, activation]


def _build_why_this_might_work(
    *,
    scenario: Scenario,
    dominant_icp: ICPProfile,
    relevant_signals: list[BehavioralSignalResponse],
    aggregate: AggregatedScenarioOutcome,
) -> list[str]:
    signal_map = {signal.signal_key: signal for signal in relevant_signals}
    top_driver = _format_driver_label(dominant_icp.decision_drivers_json[0]) if dominant_icp.decision_drivers_json else "Perceived value"
    scenario_type = str(scenario.scenario_type)

    if scenario_type == ScenarioType.pricing_decrease.value:
        bullets = [
            f"{SIGNAL_LABELS['priceSensitivity']} is {_level_word(signal_map.get('priceSensitivity', _default_signal()).value_1_to_5)}, so lower pricing should affect evaluation quickly.",
            f"{SIGNAL_LABELS['switchingFriction']} is {_level_word(signal_map.get('switchingFriction', _default_signal()).value_1_to_5)}, which reduces hesitation once value feels obvious.",
            f"{top_driver} is a top decision driver, so a cheaper offer has room to move conversion if perceived value holds.",
        ]
    elif scenario_type == ScenarioType.pricing_increase.value:
        bullets = [
            f"{SIGNAL_LABELS['switchingFriction']} gives some insulation, but {SIGNAL_LABELS['priceSensitivity'].lower()} remains important for this segment.",
            f"{top_driver} will determine whether the price step-up feels justified.",
            f"{aggregate.projected_downgrade_pct:.1f}% modeled downgrade exposure suggests packaging clarity matters as much as price.",
        ]
    elif scenario_type == ScenarioType.feature_removal.value:
        bullets = [
            f"{SIGNAL_LABELS['proofRequirement']} is {_level_word(signal_map.get('proofRequirement', _default_signal()).value_1_to_5)}, so the buyer needs a clear story for what still makes the offer complete.",
            f"{SIGNAL_LABELS['retentionStability']} is {_level_word(signal_map.get('retentionStability', _default_signal()).value_1_to_5)}, which makes perceived value erosion especially visible at renewal.",
            f"{top_driver} matters here, so removing value without replacement will surface quickly in the simulation.",
        ]
    else:
        bullets = [
            f"{SIGNAL_LABELS['timeToValueExpectation']} is {_level_word(signal_map.get('timeToValueExpectation', _default_signal()).value_1_to_5)}, so the segment responds when value becomes obvious fast.",
            f"{SIGNAL_LABELS['implementationTolerance']} is {_level_word(signal_map.get('implementationTolerance', _default_signal()).value_1_to_5)}, which shapes how much packaging or rollout complexity the segment will accept.",
            f"{top_driver} is central, so the scenario works only if the changed offer feels easier to justify than the current setup.",
        ]
    return [truncate_text(normalize_text(item), 120) for item in bullets[:3]]


def _build_tradeoffs(scenario: Scenario) -> list[str]:
    scenario_type = str(scenario.scenario_type)
    if scenario_type == ScenarioType.pricing_decrease.value:
        return [
            "Lower pricing can anchor buyers to discount expectations.",
            "Revenue per account falls if conversion uplift is weaker than expected.",
            "Cheaper entry can bring in lower-intent signups.",
        ]
    if scenario_type == ScenarioType.pricing_increase.value:
        return [
            "Higher pricing can increase downgrade behavior before churn.",
            "Perceived premium positioning only holds if value remains obvious.",
            "Renewal conversations may take longer and require stronger proof.",
        ]
    if scenario_type == ScenarioType.feature_removal.value:
        return [
            "Feature removal can weaken trust even among retained accounts.",
            "Competitor evaluation rises when the removed capability mattered to adoption.",
            "Support load increases if customers feel forced into workarounds.",
        ]
    if scenario_type == ScenarioType.unbundling.value:
        return [
            "Separating services can reduce clarity if packaging feels fragmented.",
            "Customers may read the move as reduced support rather than better focus.",
            "Savings only matter if the lighter package still feels complete enough.",
        ]
    return [
        "New packaging adds decision complexity during evaluation.",
        "Proof burden rises if the extra value is not obvious quickly.",
        "Upside depends on positioning staying clearer than the old offer.",
    ]


def _build_execution_effort(scenario: Scenario) -> ScenarioExecutionEffortResponse:
    scenario_type = str(scenario.scenario_type)
    if scenario_type in {ScenarioType.pricing_increase.value, ScenarioType.pricing_decrease.value}:
        return ScenarioExecutionEffortResponse(
            level="low",
            explanation="Pricing and packaging messaging can be tested without changing core delivery.",
        )
    if scenario_type in {ScenarioType.premium_feature_addition.value, ScenarioType.bundling.value, ScenarioType.unbundling.value}:
        return ScenarioExecutionEffortResponse(
            level="medium",
            explanation="Go-to-market, packaging, and enablement work all need alignment before launch.",
        )
    return ScenarioExecutionEffortResponse(
        level="high",
        explanation="Removing value usually requires product, support, and renewal-motion changes at once.",
    )


def _build_scenario_metadata(scenario: Scenario) -> ScenarioMetadataResponse:
    input_parameters = dict(scenario.input_parameters_json)
    return ScenarioMetadataResponse(
        market=_optional_text(input_parameters.get("market")),
        service_name=_optional_text(input_parameters.get("service_name")),
        plan_tier=_optional_text(input_parameters.get("plan_tier")),
        billing_period=_optional_text(input_parameters.get("billing_period")),
        scenario_tags=_build_scenario_tags(scenario),
    )


def _build_scenario_tags(scenario: Scenario) -> list[str]:
    scenario_type = str(scenario.scenario_type)
    if scenario_type in {ScenarioType.pricing_increase.value, ScenarioType.pricing_decrease.value}:
        return ["pricing", "monetization", "conversion"]
    if scenario_type == ScenarioType.feature_removal.value:
        return ["packaging", "retention", "risk"]
    if scenario_type == ScenarioType.premium_feature_addition.value:
        return ["upsell", "packaging", "proof"]
    if scenario_type == ScenarioType.bundling.value:
        return ["bundle", "value-narrative", "activation"]
    return ["unbundling", "clarity", "retention"]


def _build_short_decision_statement(scenario: Scenario) -> str:
    params = scenario.input_parameters_json
    scenario_type = str(scenario.scenario_type)
    if scenario_type == ScenarioType.pricing_increase.value:
        return f"Increase pricing by {params.get('price_change_percent', 0)}% for the current package."
    if scenario_type == ScenarioType.pricing_decrease.value:
        return f"Decrease pricing by {params.get('price_change_percent', 0)}% to test conversion lift."
    if scenario_type == ScenarioType.feature_removal.value:
        return f"Remove {params.get('removed_feature', 'a feature')} from the offer."
    if scenario_type == ScenarioType.premium_feature_addition.value:
        return f"Gate {params.get('premium_feature', 'the premium capability')} behind a higher tier."
    if scenario_type == ScenarioType.bundling.value:
        return f"Bundle {params.get('bundle_name', 'additional value')} into the package."
    if scenario_type == ScenarioType.unbundling.value:
        return f"Unbundle {params.get('service_name', 'the service add-on')} from the core offer."
    return truncate_text(normalize_text(scenario.title), 110)


def _score_scenario_review(
    review_view: ScenarioReviewViewResponse,
    execution_effort: ScenarioExecutionEffortResponse,
) -> float:
    metric_map = {item.metric_key: _impact_center(item) for item in review_view.expected_impact}
    effort_modifier = {"low": 4.0, "medium": 0.0, "high": -4.0}[execution_effort.level]
    score = (
        metric_map.get("revenue", 0.0) * 1.4
        + metric_map.get("conversion", 0.0) * 0.8
        + metric_map.get("activation_speed", 0.0) * 0.35
        - max(0.0, metric_map.get("churn_risk", 0.0)) * 1.6
        + min(0.0, metric_map.get("churn_risk", 0.0)) * -0.4
        + effort_modifier
    )
    return round(score, 2)


def _build_recommendation(
    *,
    review_view: ScenarioReviewViewResponse,
    ranking_score: float,
    priority_rank: int,
    total: int,
) -> ScenarioRecommendationResponse:
    effort = review_view.execution_effort.level
    if priority_rank == 1 and effort == "low" and ranking_score > 0:
        label = "Recommended first"
    elif priority_rank == 1:
        label = "Highest expected upside"
    elif ranking_score > 0 and effort == "low":
        label = "High-impact, low-effort"
    elif ranking_score > 0:
        label = "Worth testing next"
    else:
        label = "Pressure-test carefully"

    revenue = next((impact for impact in review_view.expected_impact if impact.metric_key == "revenue"), None)
    churn = next((impact for impact in review_view.expected_impact if impact.metric_key == "churn_risk"), None)
    reason = (
        f"Ranked #{priority_rank} of {total} because modeled upside stays ahead of churn and execution drag."
        if ranking_score > 0
        else f"Ranked #{priority_rank} of {total} because the downside case is more visible than the upside."
    )
    if revenue and churn:
        reason = (
            f"Ranked #{priority_rank} of {total}: revenue is {_direction_copy(revenue.direction)} while churn risk is {_direction_copy(churn.direction)}."
        )
    return ScenarioRecommendationResponse(
        priority_rank=priority_rank,
        recommendation_label=label,
        recommendation_reason=reason,
    )


def _select_relevant_signals(
    signals: dict[str, BehavioralSignalResponse],
    *,
    scenario_type: str,
) -> list[BehavioralSignalResponse]:
    mapping: dict[str, tuple[str, ...]] = {
        ScenarioType.pricing_increase.value: ("priceSensitivity", "switchingFriction", "retentionStability"),
        ScenarioType.pricing_decrease.value: ("priceSensitivity", "switchingFriction", "timeToValueExpectation"),
        ScenarioType.feature_removal.value: ("proofRequirement", "retentionStability", "switchingFriction"),
        ScenarioType.premium_feature_addition.value: ("proofRequirement", "implementationTolerance", "timeToValueExpectation"),
        ScenarioType.bundling.value: ("timeToValueExpectation", "implementationTolerance", "proofRequirement"),
        ScenarioType.unbundling.value: ("priceSensitivity", "implementationTolerance", "retentionStability"),
    }
    ordered_keys = mapping.get(scenario_type, SIGNAL_ORDER[:3])
    return [signals[key] for key in ordered_keys if key in signals]


def _impact_range(
    *,
    label: str,
    metric_key: str,
    center: float,
    confidence: str,
    invert_business_direction: bool = False,
) -> ScenarioExpectedImpactResponse:
    spread = max(1.0, round(max(abs(center) * 0.35, 1.0), 1))
    minimum = round(center - spread, 1)
    maximum = round(center + spread, 1)
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    direction = "neutral"
    if center > 0.4:
        direction = "negative" if invert_business_direction else "positive"
    elif center < -0.4:
        direction = "positive" if invert_business_direction else "negative"
    elif abs(center) > 0.1:
        direction = "mixed"
    return ScenarioExpectedImpactResponse(
        metric_key=metric_key,
        label=label,
        direction=direction,
        min_change_percent=minimum,
        max_change_percent=maximum,
        confidence=confidence,
    )


def _weighted_average_signals(
    signals: dict[str, dict[str, BehavioralSignalResponse]],
    profiles: list[ICPProfile],
) -> dict[str, float]:
    totals = {key: 0.0 for key in SIGNAL_ORDER}
    total_weight = sum(max(0.01, profile.segment_weight) for profile in profiles)
    for profile in profiles:
        weight = max(0.01, profile.segment_weight)
        profile_signals = signals.get(profile.id, {})
        for signal_key in SIGNAL_ORDER:
            if signal_key in profile_signals:
                totals[signal_key] += profile_signals[signal_key].value_1_to_5 * weight
    if total_weight == 0:
        return {key: 3.0 for key in SIGNAL_ORDER}
    return {key: totals[key] / total_weight for key in SIGNAL_ORDER}


def _derive_conversion_change_pct(scenario_type: str, price_change: float, signals: dict[str, float]) -> float:
    price = signals["priceSensitivity"] / 5
    switching = signals["switchingFriction"] / 5
    proof = signals["proofRequirement"] / 5
    if scenario_type == ScenarioType.pricing_decrease.value:
        return round(price_change * (0.8 + price * 1.1 + (1 - switching) * 0.5), 1)
    if scenario_type == ScenarioType.pricing_increase.value:
        return round(-price_change * (0.65 + price * 0.95 + (1 - switching) * 0.35), 1)
    if scenario_type == ScenarioType.feature_removal.value:
        return round(-7.5 - proof * 3.5, 1)
    if scenario_type == ScenarioType.premium_feature_addition.value:
        return round(4.0 + (1 - proof) * 4.0 - price * 1.5, 1)
    if scenario_type == ScenarioType.bundling.value:
        return round(3.2 + (1 - proof) * 2.5 + (1 - switching) * 1.5, 1)
    return round(2.5 + price * 2.0 - proof * 1.2, 1)


def _derive_activation_change_pct(scenario_type: str, signals: dict[str, float]) -> float:
    ttv = signals["timeToValueExpectation"] / 5
    implementation = signals["implementationTolerance"] / 5
    complexity = {
        ScenarioType.pricing_increase.value: 0.4,
        ScenarioType.pricing_decrease.value: 0.3,
        ScenarioType.feature_removal.value: 0.9,
        ScenarioType.premium_feature_addition.value: 0.8,
        ScenarioType.bundling.value: 0.85,
        ScenarioType.unbundling.value: 0.75,
    }.get(scenario_type, 0.5)
    center = (implementation - ttv) * complexity * 10
    return round(center, 1)


def _derive_churn_risk_change_pct(
    scenario_type: str,
    aggregate: AggregatedScenarioOutcome,
    signals: dict[str, float],
) -> float:
    retention_risk = (6 - signals["retentionStability"]) / 5
    proof = signals["proofRequirement"] / 5
    baseline = aggregate.projected_churn_pct * 0.18
    if scenario_type == ScenarioType.pricing_decrease.value:
        return round(-max(1.0, baseline * 0.8), 1)
    if scenario_type == ScenarioType.pricing_increase.value:
        return round(baseline + retention_risk * 2.6 + proof * 1.2, 1)
    if scenario_type == ScenarioType.feature_removal.value:
        return round(baseline + retention_risk * 3.4 + proof * 1.6, 1)
    if scenario_type == ScenarioType.unbundling.value:
        return round(baseline + retention_risk * 1.8, 1)
    return round(max(0.3, baseline * 0.6 + proof * 0.8), 1)


def _selected_drivers(icp: GeneratedICP) -> list[str]:
    ordered = list(icp.decision_drivers)
    for driver in icp.driver_weights:
        if driver not in ordered:
            ordered.append(driver)
    return ordered


def _normalize_signal(value: float, min_value: float, max_value: float) -> int:
    if min_value == max_value:
        return 3
    ratio = (value - min_value) / (max_value - min_value)
    ratio = max(0.0, min(1.0, ratio))
    return max(SIGNAL_SCALE_MIN, min(SIGNAL_SCALE_MAX, round(ratio * 4) + 1))


def _compress_list(values: list[str], *, limit: int) -> list[str]:
    return [truncate_text(normalize_text(value), 80) for value in dedupe_preserve_order(values)[:limit]]


def _split_sentences(value: str) -> list[str]:
    normalized = normalize_text(value)
    if not normalized:
        return []
    chunks = [chunk.strip(" .") for chunk in normalized.replace(";", ".").split(".")]
    return [chunk for chunk in chunks if chunk]


def _format_driver_label(driver: str) -> str:
    return " ".join(segment.capitalize() for segment in driver.split("_"))


def _confidence_label(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.6:
        return "medium"
    return "low"


def _level_word(level: int) -> str:
    if level >= 4:
        return "high"
    if level == 3:
        return "medium"
    return "low"


def _severity_from_level(level: int) -> str:
    if level >= 4:
        return "high"
    if level == 3:
        return "medium"
    return "low"


def _impact_center(item: ScenarioExpectedImpactResponse) -> float:
    return (item.min_change_percent + item.max_change_percent) / 2


def _direction_copy(direction: str) -> str:
    if direction == "positive":
        return "supportive"
    if direction == "negative":
        return "fragile"
    if direction == "mixed":
        return "mixed"
    return "neutral"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = normalize_text(str(value))
    return normalized or None


def _ordered_entity_key(item: Any) -> tuple[int, datetime | None]:
    return (int(getattr(item, "display_order", 0) or 0), getattr(item, "created_at", None))


def _default_signal() -> BehavioralSignalResponse:
    return BehavioralSignalResponse(
        signal_key="unknown",
        label="Unknown",
        value_1_to_5=3,
        editable=False,
        derived=True,
        source_field=None,
    )


def _entity_identifier(item: Any, *, prefix: str) -> str:
    raw_id = getattr(item, "id", None)
    if raw_id:
        return str(raw_id)
    return f"{prefix}-{int(getattr(item, 'display_order', 0) or 0)}"
