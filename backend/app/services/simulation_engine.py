from __future__ import annotations

from collections import defaultdict

from app.services.domain_types import GeneratedICP, GeneratedScenario, ProductUnderstanding, SimulationComputationResult


class SimulationEngine:
    ENGINE_VERSION = "utility-v1"

    def simulate(
        self,
        *,
        understanding: ProductUnderstanding,
        icp: GeneratedICP,
        scenario: GeneratedScenario,
    ) -> SimulationComputationResult:
        baseline_scores = self._baseline_scores(understanding, icp)
        driver_impacts = self._scenario_driver_impacts(icp, scenario, understanding)
        utility_before = round(sum(icp.driver_weights.get(driver, 0.0) * baseline_scores.get(driver, 0.6) for driver in icp.decision_drivers), 4)
        adjusted_scores = {
            driver: min(1.0, max(0.0, baseline_scores.get(driver, 0.6) + driver_impacts.get(driver, 0.0)))
            for driver in set(icp.decision_drivers) | set(driver_impacts)
        }
        utility_after = round(sum(icp.driver_weights.get(driver, 0.0) * adjusted_scores.get(driver, 0.6) for driver in icp.decision_drivers), 4)
        delta = round(utility_after - utility_before, 4)
        reaction = self._classify_reaction(icp, delta)
        baseline_revenue = self._baseline_revenue(understanding, scenario)
        revenue_delta = round(self._estimate_revenue_delta(icp, reaction, baseline_revenue, scenario), 2)
        perception_shift = round(max(-1.0, min(1.0, delta * 4.5)), 3)
        second_order_effects = self._second_order_effects(scenario, reaction)
        explanation = self._build_explanation(icp, scenario, delta, reaction, driver_impacts)
        assumptions = {
            "baseline_scores": baseline_scores,
            "adjusted_scores": adjusted_scores,
            "reaction_thresholds": {
                "churn_threshold": icp.churn_threshold - (icp.switching_cost * 0.05),
                "downgrade_threshold": min(
                    -0.02,
                    (icp.churn_threshold - (icp.switching_cost * 0.05)) / 2 + 0.02,
                ),
                "upgrade_threshold": icp.retention_threshold + (0.08 - icp.switching_cost * 0.03),
            },
            "baseline_revenue_per_account": baseline_revenue,
        }
        return SimulationComputationResult(
            reaction=reaction,
            utility_score_before=utility_before,
            utility_score_after=utility_after,
            delta_score=delta,
            revenue_delta=revenue_delta,
            perception_shift=perception_shift,
            second_order_effects=second_order_effects,
            driver_impacts={key: round(value, 4) for key, value in driver_impacts.items()},
            explanation=explanation,
            assumptions=assumptions,
        )

    def _baseline_scores(self, understanding: ProductUnderstanding, icp: GeneratedICP) -> dict[str, float]:
        feature_strength = min(0.9, 0.58 + len(understanding.feature_clusters) * 0.05)
        base = defaultdict(
            lambda: 0.64,
            {
                "price_affordability": 0.72 if understanding.pricing_model == "tiered_subscription" else 0.64,
                "value_for_money": 0.7,
                "content_access": 0.82 if understanding.subcategory == "Video Streaming" else feature_strength,
                "mobile_experience": 0.78 if understanding.subcategory == "Video Streaming" else 0.66,
                "brand_habit": 0.84 if understanding.company_name.lower() == "netflix" else 0.65,
                "video_quality": 0.76 if understanding.subcategory == "Video Streaming" else 0.64,
                "family_fit": 0.74 if understanding.subcategory == "Video Streaming" else 0.62,
                "device_support": 0.8 if understanding.subcategory == "Video Streaming" else 0.68,
                "regional_content": 0.66 if understanding.subcategory == "Video Streaming" else 0.58,
                "feature_completeness": feature_strength,
                "automation_coverage": feature_strength,
                "analytics_depth": 0.68 if understanding.subcategory in {"Analytics", "CRM"} else 0.6,
                "implementation_complexity": 0.58,
                "support_reliability": 0.66,
                "team_enablement": 0.68 if understanding.category == "B2B Software" else 0.54,
                "budget_predictability": 0.67,
            },
        )
        if not understanding.raw_extracted_json.get("pricing_clues"):
            base["price_affordability"] -= 0.06
            base["budget_predictability"] -= 0.04
        if understanding.confidence_score < 0.65:
            base["feature_completeness"] -= 0.05
        return {driver: round(base[driver], 4) for driver in icp.decision_drivers}

    def _scenario_driver_impacts(
        self,
        icp: GeneratedICP,
        scenario: GeneratedScenario,
        understanding: ProductUnderstanding,
    ) -> dict[str, float]:
        impacts: dict[str, float] = {}
        scenario_type = scenario.scenario_type
        price_change = float(scenario.input_parameters.get("price_change_percent") or scenario.input_parameters.get("bundle_price_change_percent") or 0)
        market_multiplier = 1.08 if str(scenario.input_parameters.get("market", "")).lower() == "india" else 1.0
        price_pressure = min(0.3, abs(price_change) / 100 * (0.95 + icp.price_sensitivity * 0.8) * market_multiplier)

        if scenario_type == "pricing_increase":
            impacts["price_affordability"] = -price_pressure
            impacts["value_for_money"] = -price_pressure * 0.82
            impacts["budget_predictability"] = -price_pressure * 0.6
            impacts["brand_habit"] = -max(0.012, price_pressure * 0.18)
        elif scenario_type == "pricing_decrease":
            impacts["price_affordability"] = price_pressure * 0.92
            impacts["value_for_money"] = price_pressure * 0.7
            impacts["budget_predictability"] = price_pressure * 0.42
        elif scenario_type == "feature_removal":
            importance = float(scenario.input_parameters.get("feature_importance", 0.6))
            impacts["feature_completeness"] = -0.22 * importance
            impacts["content_access"] = -0.18 * importance
            impacts["convenience"] = -0.12 * importance
            impacts["brand_habit"] = -0.05 * importance
            if "streams" in str(scenario.input_parameters.get("removed_feature", "")).lower():
                impacts["family_fit"] = -0.18 * importance
                impacts["device_support"] = -0.12 * importance
        elif scenario_type == "premium_feature_addition":
            impacts["feature_completeness"] = 0.16
            impacts["content_access"] = 0.12
            impacts["video_quality"] = 0.08
            if price_change:
                impacts["price_affordability"] = -min(0.18, abs(price_change) / 100 * (0.72 + icp.price_sensitivity * 0.4))
        elif scenario_type == "bundling":
            impacts["feature_completeness"] = 0.14
            impacts["convenience"] = 0.08
            impacts["content_access"] = 0.1
            if price_change:
                impacts["price_affordability"] = -min(0.12, abs(price_change) / 100 * (0.7 + icp.price_sensitivity * 0.35))
                impacts["value_for_money"] = 0.04
        elif scenario_type == "unbundling":
            impacts["price_affordability"] = 0.08
            impacts["budget_predictability"] = 0.06
            impacts["feature_completeness"] = -0.12
            impacts["convenience"] = -0.08

        if understanding.subcategory == "Video Streaming" and scenario_type in {"pricing_increase", "feature_removal"}:
            impacts["mobile_experience"] = impacts.get("mobile_experience", 0.0) - 0.03 * icp.price_sensitivity
        return impacts

    def _classify_reaction(self, icp: GeneratedICP, delta: float) -> str:
        churn_threshold = icp.churn_threshold - (icp.switching_cost * 0.05)
        downgrade_threshold = min(-0.02, churn_threshold / 2 + 0.02)
        upgrade_threshold = icp.retention_threshold + (0.08 - icp.switching_cost * 0.03)
        if delta <= churn_threshold:
            return "churn"
        if delta <= downgrade_threshold:
            return "downgrade"
        if delta >= upgrade_threshold:
            return "upgrade"
        return "retain"

    def _baseline_revenue(self, understanding: ProductUnderstanding, scenario: GeneratedScenario) -> float:
        if scenario.input_parameters.get("current_price_estimate"):
            return float(scenario.input_parameters["current_price_estimate"])
        if understanding.subcategory == "Video Streaming":
            return 499.0
        if understanding.category == "B2B Software":
            return 1200.0
        return 100.0

    def _estimate_revenue_delta(self, icp: GeneratedICP, reaction: str, baseline_revenue: float, scenario: GeneratedScenario) -> float:
        segment_customers = 100 * icp.segment_weight
        price_change = float(scenario.input_parameters.get("price_change_percent") or scenario.input_parameters.get("bundle_price_change_percent") or 0) / 100
        after_price = baseline_revenue * (1 + price_change)
        if scenario.scenario_type == "feature_removal":
            after_price = baseline_revenue
        if scenario.scenario_type == "premium_feature_addition" and price_change == 0:
            after_price = baseline_revenue * 1.08
        if scenario.scenario_type == "unbundling" and price_change == 0:
            after_price = baseline_revenue * 0.94

        if reaction == "retain":
            per_customer_after = after_price
        elif reaction == "upgrade":
            per_customer_after = after_price * 1.15
        elif reaction == "downgrade":
            per_customer_after = baseline_revenue * max(0.52, 0.8 - icp.price_sensitivity * 0.22)
        else:
            per_customer_after = 0
        return (per_customer_after - baseline_revenue) * segment_customers

    def _second_order_effects(self, scenario: GeneratedScenario, reaction: str) -> list[str]:
        scenario_type = scenario.scenario_type
        if scenario_type == "pricing_increase":
            base = [
                "increased plan comparison behavior",
                "higher downgrade to lower tier before churn",
                "greater price scrutiny among mixed-device households",
            ]
        elif scenario_type == "feature_removal":
            base = [
                "support complaints rise around removed capability",
                "more explicit competitor evaluation during renewal",
                "higher willingness to test partial substitutes",
            ]
        elif scenario_type == "bundling":
            base = [
                "upgrade consideration shifts toward bundle value framing",
                "more internal debate on whether extra bundle usage is real",
                "premium tier messaging becomes more important",
            ]
        else:
            base = [
                "buyers spend more time validating package fit",
                "value narratives become more central in renewal discussions",
                "segment sensitivity diverges more clearly",
            ]
        if reaction == "upgrade":
            return base[:2] + ["positive word-of-mouth increases among satisfied evaluators"]
        if reaction == "churn":
            return base[:2] + ["reactivation becomes harder after perceived trust erosion"]
        return base

    def _build_explanation(
        self,
        icp: GeneratedICP,
        scenario: GeneratedScenario,
        delta: float,
        reaction: str,
        driver_impacts: dict[str, float],
    ) -> str:
        ordered_impacts = sorted(driver_impacts.items(), key=lambda item: abs(item[1]), reverse=True)
        top_impacts = ", ".join(f"{driver} {impact:+.2f}" for driver, impact in ordered_impacts[:3])
        return (
            f"{icp.name} lands on {reaction} because the scenario changes weighted utility by {delta:+.2f}. "
            f"The strongest drivers were {top_impacts or 'minimal direct driver movement'}. "
            f"Price sensitivity={icp.price_sensitivity:.2f}, switching_cost={icp.switching_cost:.2f}."
        )
