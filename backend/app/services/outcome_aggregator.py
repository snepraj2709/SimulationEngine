from __future__ import annotations

from collections import Counter

from app.services.domain_types import AggregatedScenarioOutcome, GeneratedICP, SimulationComputationResult


class OutcomeAggregator:
    def aggregate(
        self,
        *,
        scenario_id: str,
        scenario_title: str,
        icps: list[GeneratedICP],
        results: list[SimulationComputationResult],
    ) -> AggregatedScenarioOutcome:
        if not icps or not results:
            return AggregatedScenarioOutcome(
                projected_retention_pct=0,
                projected_downgrade_pct=0,
                projected_upgrade_pct=0,
                projected_churn_pct=0,
                estimated_revenue_delta_pct=0,
                weighted_revenue_delta=0,
                perception_shift_score=0,
                perception_shift_label="neutral",
                highest_risk_icps=[],
                top_negative_drivers=[],
                top_positive_drivers=[],
                second_order_effects=[],
            )

        reaction_weights = Counter[str]()
        total_baseline_revenue = 0.0
        weighted_revenue_delta = 0.0
        weighted_perception = 0.0
        risk_rows: list[tuple[float, str]] = []
        negative_drivers = Counter[str]()
        positive_drivers = Counter[str]()
        second_order_effects = Counter[str]()

        for icp, result in zip(icps, results, strict=True):
            weight = icp.segment_weight
            segment_customers = 100 * weight
            reaction_weights[result.reaction] += weight
            baseline_revenue_per_account = result.assumptions.get("baseline_revenue_per_account")
            if baseline_revenue_per_account is not None:
                total_baseline_revenue += max(1.0, float(baseline_revenue_per_account)) * segment_customers
            else:
                total_baseline_revenue += max(1.0, 100 * weight)
            weighted_revenue_delta += result.revenue_delta
            weighted_perception += result.perception_shift * weight
            risk_rows.append((result.delta_score, icp.name))
            for driver, impact in result.driver_impacts.items():
                if impact < 0:
                    negative_drivers[driver] += abs(impact) * weight
                elif impact > 0:
                    positive_drivers[driver] += impact * weight
            for effect in result.second_order_effects:
                second_order_effects[effect] += weight

        revenue_delta_pct = round((weighted_revenue_delta / total_baseline_revenue) * 100, 2) if total_baseline_revenue else 0.0
        perception_shift_score = round(weighted_perception, 3)
        if perception_shift_score > 0.12:
            perception_label = "positive"
        elif perception_shift_score < -0.12:
            perception_label = "negative"
        else:
            perception_label = "neutral"

        highest_risk = [name for _, name in sorted(risk_rows, key=lambda item: item[0])[:2]]
        return AggregatedScenarioOutcome(
            projected_retention_pct=round(reaction_weights.get("retain", 0) * 100, 1),
            projected_downgrade_pct=round(reaction_weights.get("downgrade", 0) * 100, 1),
            projected_upgrade_pct=round(reaction_weights.get("upgrade", 0) * 100, 1),
            projected_churn_pct=round(reaction_weights.get("churn", 0) * 100, 1),
            estimated_revenue_delta_pct=revenue_delta_pct,
            weighted_revenue_delta=round(weighted_revenue_delta, 2),
            perception_shift_score=perception_shift_score,
            perception_shift_label=perception_label,
            highest_risk_icps=highest_risk,
            top_negative_drivers=[driver.replace("_", " ") for driver, _ in negative_drivers.most_common(3)],
            top_positive_drivers=[driver.replace("_", " ") for driver, _ in positive_drivers.most_common(3)],
            second_order_effects=[effect for effect, _ in second_order_effects.most_common(3)],
        )
