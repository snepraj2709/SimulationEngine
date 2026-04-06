from app.services.simulation_engine import SimulationEngine
from app.tests.factories import sample_generated_icps, sample_generated_scenarios, sample_product_understanding


def test_simulation_engine_price_increase_hits_price_sensitive_segment() -> None:
    understanding = sample_product_understanding()
    icp = sample_generated_icps()[1]
    scenario = sample_generated_scenarios()[0]

    result = SimulationEngine().simulate(understanding=understanding, icp=icp, scenario=scenario)

    assert result.delta_score < 0
    assert result.reaction == "retain"
    assert result.driver_impacts["price_affordability"] < 0


def test_simulation_engine_finance_reviewer_is_more_exposed_to_price_change() -> None:
    understanding = sample_product_understanding()
    ops_lead, _, finance_reviewer = sample_generated_icps()
    scenario = sample_generated_scenarios()[0]

    ops_result = SimulationEngine().simulate(understanding=understanding, icp=ops_lead, scenario=scenario)
    finance_result = SimulationEngine().simulate(understanding=understanding, icp=finance_reviewer, scenario=scenario)

    assert finance_result.delta_score < ops_result.delta_score
    assert finance_result.driver_impacts["budget_predictability"] < 0
