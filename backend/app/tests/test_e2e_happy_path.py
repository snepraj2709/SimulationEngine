from app.tests.factories import sample_generated_icps, sample_generated_scenarios, sample_product_understanding, sample_scrape_result
from fastapi.testclient import TestClient


def test_full_happy_path(client: TestClient, monkeypatch) -> None:
    async def fake_scrape(self, normalized_url: str):
        return sample_scrape_result(normalized_url)

    async def fake_understanding(self, scrape_result, *, user_identifier: str):
        return sample_product_understanding()

    async def fake_artifacts(self, understanding, *, user_identifier: str):
        return sample_generated_icps(), sample_generated_scenarios()

    monkeypatch.setattr("app.services.scraper_service.ScraperService.scrape", fake_scrape)
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_product_understanding",
        fake_understanding,
    )
    monkeypatch.setattr(
        "app.services.llm.openai_analysis_service.OpenAIAnalysisService.generate_icps_and_scenarios",
        fake_artifacts,
    )

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "founder@example.com",
            "password": "StrongPass123!",
            "full_name": "Founder",
        },
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_analysis = client.post(
        "/api/v1/analyses",
        json={"url": "https://acme.example/", "run_async": False},
        headers=headers,
    )
    assert create_analysis.status_code == 202
    analysis_id = create_analysis.json()["analysis"]["id"]

    detail = client.get(f"/api/v1/analyses/{analysis_id}", headers=headers).json()
    scenario = detail["scenarios"][0]

    rerun = client.post(
        f"/api/v1/analyses/{analysis_id}/scenarios/{scenario['id']}/simulate",
        json={"input_overrides": {"price_change_percent": 15}, "run_version": "2"},
        headers=headers,
    )
    assert rerun.status_code == 200
    run_id = rerun.json()["id"]
    assert rerun.json()["summary"]["projected_churn_pct"] >= 0

    feedback = client.post(
        "/api/v1/feedback",
        json={
            "analysis_id": analysis_id,
            "scenario_id": scenario["id"],
            "simulation_run_id": run_id,
            "feedback_type": "thumbs_up",
            "comment": "Useful segmentation for pricing review.",
        },
        headers=headers,
    )
    assert feedback.status_code == 201
    assert feedback.json()["feedback_type"] == "thumbs_up"
