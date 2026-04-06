from __future__ import annotations

from app.services.domain_types import GeneratedICP, GeneratedScenario, ProductUnderstanding


class ScenarioGenerationService:
    def generate(self, understanding: ProductUnderstanding, _icps: list[GeneratedICP]) -> list[GeneratedScenario]:
        if understanding.subcategory == "Video Streaming":
            return self._video_streaming_scenarios()
        if understanding.category == "B2B Software":
            return self._b2b_scenarios()
        return self._generic_scenarios(understanding)

    def _video_streaming_scenarios(self) -> list[GeneratedScenario]:
        return [
            GeneratedScenario(
                title="Increase premium plan price in India by 12%",
                scenario_type="pricing_increase",
                description="Test how a visible premium-tier increase in India changes retention, downgrade behavior, and price scrutiny.",
                input_parameters={
                    "market": "India",
                    "plan_tier": "premium",
                    "price_change_percent": 12,
                    "current_price_estimate": 649,
                },
            ),
            GeneratedScenario(
                title="Add a premium sports and live-events bundle",
                scenario_type="bundling",
                description="Evaluate if a paid bundle increases perceived value enough to drive upgrades among high-engagement households.",
                input_parameters={
                    "bundle_name": "sports_plus",
                    "bundle_price_change_percent": 8,
                    "current_price_estimate": 649,
                },
            ),
            GeneratedScenario(
                title="Remove simultaneous extra stream access from mid-tier plans",
                scenario_type="feature_removal",
                description="Measure churn and downgrade risk if household concurrency becomes more restrictive.",
                input_parameters={
                    "removed_feature": "simultaneous extra streams",
                    "feature_importance": 0.72,
                },
            ),
        ]

    def _b2b_scenarios(self) -> list[GeneratedScenario]:
        return [
            GeneratedScenario(
                title="Increase annual contract price by 10%",
                scenario_type="pricing_increase",
                description="Test how procurement sensitivity changes at renewal for an across-the-board contract increase.",
                input_parameters={"price_change_percent": 10, "billing_period": "annual", "current_price_estimate": 1200},
            ),
            GeneratedScenario(
                title="Gate advanced analytics behind a premium tier",
                scenario_type="premium_feature_addition",
                description="Estimate upgrade conversion versus value pushback when advanced analytics move into a premium package.",
                input_parameters={"premium_feature": "advanced analytics", "price_change_percent": 14, "current_price_estimate": 1200},
            ),
            GeneratedScenario(
                title="Unbundle implementation support from the core package",
                scenario_type="unbundling",
                description="Test whether separating onboarding and support drives price clarity or trust erosion.",
                input_parameters={"service_name": "implementation support", "price_change_percent": -6, "current_price_estimate": 1200},
            ),
        ]

    def _generic_scenarios(self, understanding: ProductUnderstanding) -> list[GeneratedScenario]:
        return [
            GeneratedScenario(
                title="Increase headline price by 8%",
                scenario_type="pricing_increase",
                description="Stress-test general willingness to absorb a moderate price increase.",
                input_parameters={"price_change_percent": 8, "current_price_estimate": 100},
            ),
            GeneratedScenario(
                title="Add a premium feature bundle",
                scenario_type="premium_feature_addition",
                description="Explore whether gated premium value creates more upgrade pull than downgrade friction.",
                input_parameters={"premium_feature": "advanced capabilities", "price_change_percent": 10, "current_price_estimate": 100},
            ),
            GeneratedScenario(
                title="Remove a lower-usage feature from the base offer",
                scenario_type="feature_removal",
                description="Estimate how sensitive each segment is to a product simplification move.",
                input_parameters={"removed_feature": "secondary workflow", "feature_importance": 0.55},
            ),
        ]
