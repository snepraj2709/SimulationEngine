from __future__ import annotations

from app.models.scenario import ScenarioType
from app.services.domain_types import GeneratedICP, GeneratedScenario, ProductUnderstanding, ScrapeResult


def sample_scrape_result(url: str = "https://acme.example/") -> ScrapeResult:
    return ScrapeResult(
        source_url=url,
        final_url=url,
        title="Acme Growth Platform",
        meta_description="Acme helps revenue teams automate onboarding, analytics, and customer expansion.",
        headings=["Automate expansion workflows", "Built for revenue teams"],
        paragraphs=[
            "Acme centralizes onboarding analytics, renewal workflows, and customer health monitoring.",
            "Plans are billed annually with custom enterprise packaging for larger teams.",
            "Revenue and customer success leaders use Acme to reduce churn and improve expansion.",
        ],
        feature_clues=["workflow automation", "renewal analytics", "customer health monitoring"],
        pricing_clues=["annual plans", "custom enterprise pricing"],
        audience_clues=["revenue teams", "customer success leaders"],
        category_clues=["automation", "analytics", "customer success"],
        raw_text="Acme centralizes onboarding analytics, renewal workflows, and customer health monitoring.",
        raw_extracted_json={
            "title": "Acme Growth Platform",
            "meta_description": "Acme helps revenue teams automate onboarding, analytics, and customer expansion.",
        },
        fetch_source="network",
    )


def sample_product_understanding() -> ProductUnderstanding:
    understanding = ProductUnderstanding(
        company_name="Acme",
        product_name="Acme Growth Platform",
        category="B2B Software",
        subcategory="Revenue Operations",
        positioning_summary="Acme helps revenue teams automate onboarding, health monitoring, and expansion workflows.",
        pricing_model="sales_led_custom_pricing",
        feature_clusters=["workflow automation", "renewal analytics", "customer health"],
        monetization_hypothesis="Annual contracts sold to revenue teams that want proactive expansion and retention workflows.",
        target_customer_signals=["revenue teams", "customer success leaders", "ops managers"],
        confidence_score=0.83,
        confidence_scores={
            "company_name": 0.9,
            "category": 0.82,
            "pricing_model": 0.78,
            "feature_clusters": 0.85,
            "target_customer_signals": 0.82,
            "positioning_summary": 0.83,
        },
        warnings=[],
        raw_extracted_json={"title": "Acme Growth Platform"},
    )
    understanding.normalized_json = understanding.model_dump()
    return understanding


def sample_generated_icps() -> list[GeneratedICP]:
    return [
        GeneratedICP(
            name="Revenue operations lead",
            description="Owns retention tooling and needs cross-functional visibility.",
            use_case="Standardize renewal and expansion workflows across customer success and sales.",
            goals=["Reduce churn", "Improve expansion coverage", "Keep reporting centralized"],
            pain_points=["Disconnected tools", "Weak renewal visibility", "High admin load"],
            decision_drivers=["team_enablement", "analytics_depth", "automation_coverage", "support_reliability"],
            driver_weights={
                "team_enablement": 0.3,
                "analytics_depth": 0.26,
                "automation_coverage": 0.24,
                "support_reliability": 0.2,
            },
            price_sensitivity=0.42,
            switching_cost=0.46,
            alternatives=["CRM workflows", "BI tools", "manual playbooks"],
            churn_threshold=-0.2,
            retention_threshold=0.07,
            adoption_friction=0.24,
            value_perception_explanation="This buyer stays when workflow breadth and reporting clarity remain strong.",
            segment_weight=0.38,
        ),
        GeneratedICP(
            name="Hands-on CS manager",
            description="Runs day-to-day health monitoring and values fast workflow execution.",
            use_case="Manage renewals, escalations, and account health with a small team.",
            goals=["Move faster", "Reduce manual work", "Keep account risk visible"],
            pain_points=["Manual tracking", "Slow reporting", "Poor automation depth"],
            decision_drivers=["automation_coverage", "feature_completeness", "price_affordability", "support_reliability"],
            driver_weights={
                "automation_coverage": 0.31,
                "feature_completeness": 0.25,
                "price_affordability": 0.23,
                "support_reliability": 0.21,
            },
            price_sensitivity=0.58,
            switching_cost=0.29,
            alternatives=["spreadsheets", "lightweight CS tools"],
            churn_threshold=-0.18,
            retention_threshold=0.05,
            adoption_friction=0.2,
            value_perception_explanation="This segment tolerates price only when automation clearly saves time.",
            segment_weight=0.34,
        ),
        GeneratedICP(
            name="Finance-aware renewal reviewer",
            description="Reviews packaging, renewal risk, and spend before expansion decisions.",
            use_case="Evaluate renewal terms and packaging fit for a growing revenue org.",
            goals=["Keep spend predictable", "Avoid vendor overlap", "Preserve flexibility"],
            pain_points=["Opaque pricing", "Overlapping features", "Unclear ROI narrative"],
            decision_drivers=["budget_predictability", "price_affordability", "feature_completeness", "implementation_complexity"],
            driver_weights={
                "budget_predictability": 0.29,
                "price_affordability": 0.27,
                "feature_completeness": 0.24,
                "implementation_complexity": 0.2,
            },
            price_sensitivity=0.67,
            switching_cost=0.24,
            alternatives=["renegotiation", "category competitors"],
            churn_threshold=-0.17,
            retention_threshold=0.04,
            adoption_friction=0.18,
            value_perception_explanation="This reviewer renews when spend remains legible and implementation risk stays low.",
            segment_weight=0.28,
        ),
    ]


def sample_generated_scenarios() -> list[GeneratedScenario]:
    return [
        GeneratedScenario(
            title="Increase annual contract price by 9%",
            scenario_type=ScenarioType.pricing_increase.value,
            description="Stress-test renewal sensitivity after a visible annual price step-up.",
            input_parameters={"price_change_percent": 9, "billing_period": "annual", "current_price_estimate": 1200},
        ),
        GeneratedScenario(
            title="Gate advanced forecasting behind a premium tier",
            scenario_type=ScenarioType.premium_feature_addition.value,
            description="Measure upgrade pull when advanced forecasting becomes a premium feature.",
            input_parameters={"premium_feature": "advanced forecasting", "price_change_percent": 12, "current_price_estimate": 1200},
        ),
        GeneratedScenario(
            title="Unbundle onboarding support from the core package",
            scenario_type=ScenarioType.unbundling.value,
            description="Test whether separating onboarding support improves price clarity or erodes trust.",
            input_parameters={"service_name": "onboarding support", "price_change_percent": -6, "current_price_estimate": 1200},
        ),
    ]
