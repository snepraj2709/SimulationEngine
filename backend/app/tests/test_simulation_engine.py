from app.services.icp_generation_service import ICPGenerationService
from app.services.product_understanding_service import ProductUnderstandingService
from app.services.scenario_generation_service import ScenarioGenerationService
from app.services.scraper_service import ScraperService
from app.services.simulation_engine import SimulationEngine


async def test_simulation_engine_price_increase_hits_price_sensitive_segment() -> None:
    scrape_result = await ScraperService().scrape("https://www.netflix.com")
    understanding = ProductUnderstandingService().build(scrape_result)
    icp = ICPGenerationService().generate(understanding)[0]
    scenario = ScenarioGenerationService().generate(understanding, [icp])[0]

    result = SimulationEngine().simulate(understanding=understanding, icp=icp, scenario=scenario)

    assert result.delta_score < 0
    assert result.reaction in {"downgrade", "churn"}
    assert "price_affordability" in result.driver_impacts


async def test_simulation_engine_premium_segment_is_less_fragile() -> None:
    scrape_result = await ScraperService().scrape("https://www.netflix.com")
    understanding = ProductUnderstandingService().build(scrape_result)
    premium_icp = ICPGenerationService().generate(understanding)[2]
    scenario = ScenarioGenerationService().generate(understanding, [premium_icp])[0]

    result = SimulationEngine().simulate(understanding=understanding, icp=premium_icp, scenario=scenario)

    assert result.delta_score < 0
    assert result.reaction in {"retain", "downgrade"}
